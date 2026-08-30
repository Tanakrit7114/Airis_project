import sqlite3
from pathlib import Path
from app.config import MEMORY_DB


class MemoryStore:
    def __init__(self, db_path=MEMORY_DB):
        Path(db_path).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as con:

            # Conversation history
            con.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Long-term memory
            con.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    memory_type TEXT NOT NULL,

                    subject TEXT NOT NULL,

                    key TEXT NOT NULL,

                    value TEXT NOT NULL,

                    importance REAL DEFAULT 0.5,

                    confidence REAL DEFAULT 0.8,

                    source TEXT DEFAULT 'conversation',

                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Fast keyword search
            con.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
                USING fts5(
                    content,
                    content='memories',
                    content_rowid='id'
                )
            """)

            con.commit()

    # -------------------------
    # Messages
    # -------------------------

    def add_message(self, role, content):

        with self._connect() as con:

            cur = con.execute(
                """
                INSERT INTO messages(role, content)
                VALUES (?, ?)
                """,
                (role, content)
            )

            rowid = cur.lastrowid

            con.commit()

    def recent(self, limit=10):

        with self._connect() as con:

            return con.execute(
                """
                SELECT role, content, created_at
                FROM messages
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()

    # -------------------------
    # Long-term memory
    # -------------------------

    def add_memory(
        self,
        memory_type,
        subject,
        key,
        value,
        importance=0.5,
        confidence=0.8,
        source="conversation"
    ):

        with self._connect() as con:

            # Update existing memory
            existing = con.execute(
                """
                SELECT id
                FROM memories
                WHERE memory_type = ?
                AND subject = ?
                AND key = ?
                """,
                (
                    memory_type,
                    subject,
                    key
                )
            ).fetchone()

            if existing:

                con.execute(
                    """
                    UPDATE memories
                    SET value = ?,
                        importance = ?,
                        confidence = ?,
                        source = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        value,
                        importance,
                        confidence,
                        source,
                        existing[0]
                    )
                )

            else:

                con.execute(
                    """
                    INSERT INTO memories(
                        memory_type,
                        subject,
                        key,
                        value,
                        importance,
                        confidence,
                        source
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        memory_type,
                        subject,
                        key,
                        value,
                        importance,
                        confidence,
                        source
                    )
                )

            con.commit()

    def search_memories(
        self,
        query,
        limit=5
    ):

        query = query.strip()

        if not query:
            return []

        with self._connect() as con:

            rows = con.execute(
                """
                SELECT
                    memory_type,
                    subject,
                    key,
                    value,
                    importance,
                    confidence
                FROM memories
                WHERE
                    key LIKE ?
                    OR value LIKE ?
                    OR subject LIKE ?
                ORDER BY
                    importance DESC,
                    updated_at DESC
                LIMIT ?
                """,
                (
                    f"%{query}%",
                    f"%{query}%",
                    f"%{query}%",
                    limit
                )
            ).fetchall()

        return rows

    def all_memories(self):

        with self._connect() as con:

            return con.execute(
                """
                SELECT
                    id,
                    memory_type,
                    subject,
                    key,
                    value,
                    importance,
                    confidence,
                    created_at,
                    updated_at
                FROM memories
                ORDER BY importance DESC
                """
            ).fetchall()
