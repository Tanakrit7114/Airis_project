# Phase 1.1 — Memory 2.0
# app/memory/store.py

import json
import sqlite3
import uuid

from pathlib import Path

from app.config import MEMORY_DB


class MemoryStore:

    def __init__(self, db_path=MEMORY_DB):
        self.db_path = db_path

        if self.db_path == ":memory:":
            self._memory_connection = sqlite3.connect(":memory:")
            self._memory_connection.row_factory = sqlite3.Row
        else:
            Path(self.db_path).parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._init_db()


    # ========================================================
    # Database connection
    # ========================================================

    def _connect(self):
        if self.db_path == ":memory:":
            return self._memory_connection

        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    # ========================================================
    # Database initialization
    # ========================================================

    def _init_db(self):

        with self._connect() as con:

            # ====================================================
            # Conversation history
            # ====================================================

            con.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # ====================================================
            # Long-term memory
            # ====================================================

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

            # ====================================================
            # Memory 2.0 migration
            # ====================================================

            existing_columns = {
                row["name"]
                for row in con.execute(
                    "PRAGMA table_info(memories)"
                ).fetchall()
            }

            migrations = {
                "memory_id": "TEXT",
                "content": "TEXT",

                # Memory lifecycle
                "status": "TEXT DEFAULT 'active'",
                "superseded_by": "TEXT",
                "content": "TEXT",
                "tags": "TEXT DEFAULT '[]'",
                "entities": "TEXT DEFAULT '[]'",
                "relationships": "TEXT DEFAULT '[]'",
                "last_accessed": "DATETIME",
                "access_count": "INTEGER DEFAULT 0",
                "decay_rate": "REAL DEFAULT 0.0",
                "expires_at": "DATETIME",
            }

            for column, definition in migrations.items():

                if column not in existing_columns:

                    con.execute(
                        f"""
                        ALTER TABLE memories
                        ADD COLUMN {column} {definition}
                        """
                    )

            # ====================================================
            # Backfill Memory 2.0 fields
            # ====================================================

            con.execute("""
                UPDATE memories
                SET memory_id = lower(
                    hex(randomblob(16))
                )
                WHERE memory_id IS NULL
            """)

            con.execute("""
                UPDATE memories
                SET content = key || ': ' || value
                WHERE content IS NULL
            """)

            con.execute("""
                UPDATE memories
                SET tags = '[]'
                WHERE tags IS NULL
            """)

            con.execute("""
                UPDATE memories
                SET entities = '[]'
                WHERE entities IS NULL
            """)

            con.execute("""
                UPDATE memories
                SET relationships = '[]'
                WHERE relationships IS NULL
            """)

            con.execute("""
                UPDATE memories
                SET access_count = 0
                WHERE access_count IS NULL
            """)

            con.execute("""
                UPDATE memories
                SET status = 'active'
                WHERE status IS NULL
            """)

            # ====================================================
            # Indexes
            # ====================================================

            con.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_memories_memory_id
                ON memories(memory_id)
            """)

            con.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_memories_type
                ON memories(memory_type)
            """)

            con.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_memories_subject_key
                ON memories(subject, key)
            """)

            con.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_memories_importance
                ON memories(importance DESC)
            """)

            con.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_memories_last_accessed
                ON memories(last_accessed)
            """)

            # ====================================================
            # Full-text search
            # ====================================================

            con.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
                USING fts5(
                    content,
                    content='memories',
                    content_rowid='id'
                )
            """)

            con.commit()

    # ========================================================
    # Messages
    # ========================================================

    def add_message(self, role, content):

        with self._connect() as con:

            con.execute(
                """
                INSERT INTO messages(role, content)
                VALUES (?, ?)
                """,
                (
                    role,
                    content,
                ),
            )

            con.commit()

    def recent(self, limit=10):

        with self._connect() as con:

            return con.execute(
                """
                SELECT
                    role,
                    content,
                    created_at
                FROM messages
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    # ========================================================
    # Add / Update Memory
    # ========================================================

    def add_memory(
        self,
        memory_type,
        subject,
        key,
        value,
        importance=0.5,
        confidence=0.8,
        source="conversation",
        tags=None,
        entities=None,
        relationships=None,
        decay_rate=0.0,
        expires_at=None,
    ):
        tags = tags if tags is not None else []
        entities = entities if entities is not None else []
        relationships = (
            relationships
            if relationships is not None
            else []
        )

        content = f"{key}: {value}"

        with self._connect() as con:

            existing = con.execute(
                """
                SELECT id, memory_id
                FROM memories
                WHERE memory_type = ?
                AND subject = ?
                AND key = ?
                LIMIT 1
                """,
                (
                    memory_type,
                    subject,
                    key,
                ),
            ).fetchone()

            # ====================================================
            # Update existing memory
            # ====================================================

            if existing:
                con.execute(
                    """
                    UPDATE memories
                    SET value = ?,
                        content = ?,
                        importance = ?,
                        confidence = ?,
                        source = ?,
                        tags = ?,
                        entities = ?,
                        relationships = ?,
                        decay_rate = ?,
                        expires_at = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        value,
                        content,
                        importance,
                        confidence,
                        source,
                        json.dumps(tags),
                        json.dumps(entities),
                        json.dumps(relationships),
                        decay_rate,
                        expires_at,
                        existing["id"],
                    ),
                )

                con.commit()

                return existing["memory_id"]

            # ====================================================
            # Insert new memory
            # ====================================================

            memory_id = str(uuid.uuid4())

            con.execute(
                """
                INSERT INTO memories(
                    memory_id,
                    memory_type,
                    subject,
                    key,
                    value,
                    content,
                    importance,
                    confidence,
                    source,
                    tags,
                    entities,
                    relationships,
                    decay_rate,
                    expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory_id,
                    memory_type,
                    subject,
                    key,
                    value,
                    content,
                    importance,
                    confidence,
                    source,
                    json.dumps(tags),
                    json.dumps(entities),
                    json.dumps(relationships),
                    decay_rate,
                    expires_at,
                ),
            )

            con.commit()

            return memory_id
                

    # ========================================================
    # Get single Memory V2
    # ========================================================

    def get_memory(self, memory_id):

        with self._connect() as con:

            row = con.execute(
                """
                SELECT
                    id,
                    memory_id,
                    memory_type,
                    subject,
                    key,
                    value,
                    content,
                    importance,
                    confidence,
                    source,
                    tags,
                    entities,
                    relationships,
                    created_at,
                    updated_at,
                    last_accessed,
                    access_count,
                    decay_rate,
                    expires_at,
                    status,
                    superseded_by
                FROM memories
                WHERE memory_id = ?
                LIMIT 1
                """,
                (memory_id,),
            ).fetchone()

            if not row:
                return None

            result = dict(row)

            self._decode_json_fields(result)

            return result
        
    # ========================================================
    # Supersede Memory
    # ========================================================

    def supersede_memory(
        self,
        old_memory_id,
        new_memory_id,
    ):
        """
        Mark an old memory as superseded by a newer memory.
        """

        if not old_memory_id:
            return False

        if not new_memory_id:
            return False

        with self._connect() as con:

            result = con.execute(
                """
                UPDATE memories
                SET
                    status = 'superseded',
                    superseded_by = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE memory_id = ?
                """,
                (
                    new_memory_id,
                    old_memory_id,
                ),
            )

            con.commit()

            return result.rowcount > 0
        
    # ========================================================
    # Active Memories
    # ========================================================

    def active_memories(self):

        with self._connect() as con:

            rows = con.execute(
                """
                SELECT
                    id,
                    memory_id,
                    memory_type,
                    subject,
                    key,
                    value,
                    content,
                    importance,
                    confidence,
                    source,
                    tags,
                    entities,
                    relationships,
                    created_at,
                    updated_at,
                    last_accessed,
                    access_count,
                    decay_rate,
                    expires_at,
                    status,
                    superseded_by
                FROM memories
                WHERE status = 'active'
                ORDER BY
                    importance DESC,
                    updated_at DESC
                """
            ).fetchall()

            memories = []

            for row in rows:

                item = dict(row)

                self._decode_json_fields(item)

                memories.append(item)

            return memories    

    # ========================================================
    # All Memories — Legacy API
    #
    # Keep this for existing tests / old code.
    # ========================================================

    def all_memories(self):

        with self._connect() as con:

            rows = con.execute(
                """
                SELECT
                    id,
                    memory_type,
                    subject,
                    key,
                    value,
                    importance,
                    confidence,
                    source,
                    created_at,
                    updated_at
                FROM memories
                ORDER BY importance DESC
                """
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

    # ========================================================
    # All Memories V2
    # ========================================================

    def all_memories_v2(self):
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT
                    id,
                    memory_id,
                    memory_type,
                    subject,
                    key,
                    value,
                    content,
                    importance,
                    confidence,
                    source,
                    tags,
                    entities,
                    relationships,
                    created_at,
                    updated_at,
                    last_accessed,
                    access_count,
                    decay_rate,
                    expires_at,
                    status,
                    superseded_by
                FROM memories
                ORDER BY
                    importance DESC,
                    updated_at DESC
                """
            ).fetchall()

            memories = []

            for row in rows:
                item = dict(row)
                self._decode_json_fields(item)
                memories.append(item)

            return memories

    # ========================================================
    # Search
    # ========================================================

    def search_memories(
        self,
        query,
        limit=8,
    ):

        query = query.strip().lower()

        if not query:
            return []

        tokens = [
            token
            for token in query.replace(
                "_",
                " ",
            ).split()
            if token
        ]

        memories = self.all_memories_v2()

        scored = []

        for memory in memories:

            text = " ".join(
                [
                    str(memory["memory_type"]),
                    str(memory["subject"]),
                    str(memory["key"]).replace(
                        "_",
                        " ",
                    ),
                    str(memory["value"]),
                ]
            ).lower()

            score = 0.0

            # Exact query
            if query in text:
                score += 10.0

            # Token matches
            for token in tokens:

                if token in text:
                    score += 2.0

            # Importance
            score += (
                float(memory["importance"])
                * 2.0
            )

            # Confidence
            score += float(
                memory["confidence"]
            )

            if score > 0:
                scored.append(
                    (
                        score,
                        memory,
                    )
                )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            memory
            for _, memory in scored[:limit]
        ]

    # ========================================================
    # Retrieve
    # ========================================================

    def retrieve(
        self,
        query,
        limit=8,
    ):
        results = self.search_memories(
            query,
            limit,
        )

        for memory in results:
            self.access_memory(memory["memory_id"])

        return results

    # ========================================================
    # Get memory by key
    # ========================================================

    def get_memory_by_key(self, key):

        with self._connect() as con:

            row = con.execute(
                """
                SELECT
                    id,
                    memory_id,
                    memory_type,
                    subject,
                    key,
                    value,
                    content,
                    importance,
                    confidence,
                    source,
                    tags,
                    entities,
                    relationships,
                    created_at,
                    updated_at,
                    last_accessed,
                    access_count,
                    decay_rate,
                    expires_at
                FROM memories
                WHERE key = ?
                LIMIT 1
                """,
                (key,),
            ).fetchone()

            if not row:
                return None

            result = dict(row)

            self._decode_json_fields(result)

            return result

    # ========================================================
    # JSON helpers
    # ========================================================

    @staticmethod
    def _decode_json_fields(memory):

        for field in (
            "tags",
            "entities",
            "relationships",
        ):

            try:

                memory[field] = json.loads(
                    memory[field] or "[]"
                )

            except (
                TypeError,
                json.JSONDecodeError,
            ):

                memory[field] = []
    
    # ========================================================
    # Memory Access
    # ========================================================

    def access_memory(self, memory_id):
        """
        Mark a memory as accessed.

        Updates:
        - last_accessed
        - access_count
        """

        with self._connect() as con:
            con.execute(
                """
                UPDATE memories
                SET
                    last_accessed = CURRENT_TIMESTAMP,
                    access_count = COALESCE(access_count, 0) + 1
                WHERE memory_id = ?
                """,
                (memory_id,),
            )

            con.commit()