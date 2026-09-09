import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from app.config import MEMORY_DB


class DashboardDB:
    def __init__(self, db_path: str = MEMORY_DB):
        self.db_path = db_path
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self):
        con = sqlite3.connect(self.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        return con

    def _init(self):
        with self.connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'general',
                    route TEXT NOT NULL DEFAULT 'memory_llm',
                    requires_confirmation INTEGER NOT NULL DEFAULT 0,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS dashboard_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ok',
                    detail TEXT NOT NULL DEFAULT '',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            con.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id, id)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON dashboard_events(event_type, created_at)")
            con.commit()

    def create_session(self, title: str | None = None) -> dict[str, Any]:
        session_id = str(uuid.uuid4())
        title = (title or "New conversation").strip() or "New conversation"
        with self.connect() as con:
            con.execute("INSERT INTO chat_sessions(id, title) VALUES (?, ?)", (session_id, title))
            con.commit()
        return self.get_session(session_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        with self.connect() as con:
            return [dict(r) for r in con.execute(
                "SELECT id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC"
            ).fetchall()]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as con:
            row = con.execute(
                "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            return dict(row) if row else None

    def delete_session(self, session_id: str) -> bool:
        with self.connect() as con:
            con.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            cur = con.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            con.commit()
            return cur.rowcount > 0

    def add_message(self, session_id: str, role: str, content: str, *, source: str, route: str,
                    requires_confirmation: bool = False, metadata: dict[str, Any] | None = None) -> int:
        with self.connect() as con:
            cur = con.execute(
                """INSERT INTO chat_messages
                   (session_id, role, content, source, route, requires_confirmation, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session_id, role, content, source, route, int(requires_confirmation), json.dumps(metadata or {}, ensure_ascii=False)),
            )
            con.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))
            con.commit()
            return int(cur.lastrowid)

    def list_messages(self, session_id: str) -> list[dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute(
                """SELECT id, role, content, source, route, requires_confirmation, metadata, created_at
                   FROM chat_messages WHERE session_id = ? ORDER BY id ASC""",
                (session_id,),
            ).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["requires_confirmation"] = bool(item["requires_confirmation"])
            try:
                item["metadata"] = json.loads(item["metadata"] or "{}")
            except json.JSONDecodeError:
                item["metadata"] = {}
            out.append(item)
        return out

    def log_event(self, event_type: str, status: str = "ok", detail: str = "", metadata: dict[str, Any] | None = None):
        with self.connect() as con:
            con.execute(
                "INSERT INTO dashboard_events(event_type, status, detail, metadata) VALUES (?, ?, ?, ?)",
                (event_type, status, detail, json.dumps(metadata or {}, ensure_ascii=False)),
            )
            con.commit()

    def events(self, event_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as con:
            if event_type:
                rows = con.execute(
                    "SELECT id, event_type, status, detail, metadata, created_at FROM dashboard_events WHERE event_type = ? ORDER BY id DESC LIMIT ?",
                    (event_type, limit),
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT id, event_type, status, detail, metadata, created_at FROM dashboard_events ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            try:
                item["metadata"] = json.loads(item["metadata"] or "{}")
            except json.JSONDecodeError:
                item["metadata"] = {}
            out.append(item)
        return out

    def analytics(self) -> dict[str, Any]:
        with self.connect() as con:
            counts = {
                "messages_today": con.execute("SELECT COUNT(*) FROM chat_messages WHERE date(created_at, 'localtime') = date('now', 'localtime') AND role = 'user'").fetchone()[0],
                "sessions": con.execute("SELECT COUNT(*) FROM chat_sessions").fetchone()[0],
                "user_messages": con.execute("SELECT COUNT(*) FROM chat_messages WHERE role = 'user'").fetchone()[0],
            }
            routes = [dict(r) for r in con.execute(
                "SELECT route, COUNT(*) AS count FROM chat_messages WHERE role = 'user' GROUP BY route ORDER BY count DESC"
            ).fetchall()]
            hourly = [dict(r) for r in con.execute(
                "SELECT strftime('%H', created_at, 'localtime') AS hour, COUNT(*) AS count FROM chat_messages WHERE role = 'user' GROUP BY hour ORDER BY hour"
            ).fetchall()]
            sources = [dict(r) for r in con.execute(
                "SELECT source, COUNT(*) AS count FROM chat_messages WHERE role = 'assistant' GROUP BY source ORDER BY count DESC"
            ).fetchall()]
        return {**counts, "routes": routes, "hourly": hourly, "sources": sources}
