# Phase 4.5 — Persistent Memory Graph

import sqlite3
from pathlib import Path

from app.config import MEMORY_DB
from app.memory.memory_link import MemoryLink


class MemoryGraphStore:
    """
    Persistent storage for MemoryGraph links.

    Stores graph relationships in the same SQLite
    database used by MemoryStore.
    """

    def __init__(self, db_path=MEMORY_DB):
        self.db_path = db_path

        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._memory_connection = None

        if self.db_path == ":memory:":
            self._memory_connection = sqlite3.connect(
                ":memory:"
            )
            self._memory_connection.row_factory = (
                sqlite3.Row
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
    # Initialization
    # ========================================================

    def _init_db(self):
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    strength REAL DEFAULT 1.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(
                        source_id,
                        target_id,
                        relation
                    )
                )
                """
            )

            con.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_memory_links_source
                ON memory_links(source_id)
                """
            )

            con.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_memory_links_target
                ON memory_links(target_id)
                """
            )

            con.commit()

    # ========================================================
    # Add
    # ========================================================

    def add_link(
        self,
        source_id,
        target_id,
        relation="related_to",
        strength=1.0,
    ):
        source_id = str(source_id)
        target_id = str(target_id)
        relation = str(relation)

        strength = max(
            0.0,
            min(1.0, float(strength)),
        )

        with self._connect() as con:
            con.execute(
                """
                INSERT INTO memory_links(
                    source_id,
                    target_id,
                    relation,
                    strength
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(
                    source_id,
                    target_id,
                    relation
                )
                DO UPDATE SET
                    strength = excluded.strength,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    source_id,
                    target_id,
                    relation,
                    strength,
                ),
            )

            con.commit()

        return MemoryLink(
            source_id,
            target_id,
            relation,
            strength,
        )

    # ========================================================
    # Remove
    # ========================================================

    def remove_link(
        self,
        source_id,
        target_id,
        relation=None,
    ):
        source_id = str(source_id)
        target_id = str(target_id)

        with self._connect() as con:
            if relation is None:
                result = con.execute(
                    """
                    DELETE FROM memory_links
                    WHERE source_id = ?
                    AND target_id = ?
                    """,
                    (
                        source_id,
                        target_id,
                    ),
                )
            else:
                result = con.execute(
                    """
                    DELETE FROM memory_links
                    WHERE source_id = ?
                    AND target_id = ?
                    AND relation = ?
                    """,
                    (
                        source_id,
                        target_id,
                        str(relation),
                    ),
                )

            con.commit()

            return result.rowcount > 0

    # ========================================================
    # Load all
    # ========================================================

    def all_links(self):
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT
                    source_id,
                    target_id,
                    relation,
                    strength
                FROM memory_links
                ORDER BY id ASC
                """
            ).fetchall()

        return [
            MemoryLink(
                row["source_id"],
                row["target_id"],
                row["relation"],
                row["strength"],
            )
            for row in rows
        ]

    def load_into_graph(self, graph):
        """
        Load all persistent links into an in-memory MemoryGraph.
        """
        if graph is None:
            return 0

        links = self.all_links()

        for link in links:
            graph.add_link(
                source_id=link.source_id,
                target_id=link.target_id,
                relation=link.relation,
                strength=link.strength,
            )

        return len(links)


    # ========================================================
    # Get outgoing links
    # ========================================================

    def get_links_from(self, memory_id):
        memory_id = str(memory_id)

        with self._connect() as con:
            rows = con.execute(
                """
                SELECT
                    source_id,
                    target_id,
                    relation,
                    strength
                FROM memory_links
                WHERE source_id = ?
                ORDER BY id ASC
                """,
                (memory_id,),
            ).fetchall()

        return [
            MemoryLink(
                row["source_id"],
                row["target_id"],
                row["relation"],
                row["strength"],
            )
            for row in rows
        ]

    # ========================================================
    # Get incoming links
    # ========================================================

    def get_links_to(self, memory_id):
        memory_id = str(memory_id)

        with self._connect() as con:
            rows = con.execute(
                """
                SELECT
                    source_id,
                    target_id,
                    relation,
                    strength
                FROM memory_links
                WHERE target_id = ?
                ORDER BY id ASC
                """,
                (memory_id,),
            ).fetchall()

        return [
            MemoryLink(
                row["source_id"],
                row["target_id"],
                row["relation"],
                row["strength"],
            )
            for row in rows
        ]

    # ========================================================
    # Clear
    # ========================================================

    def clear(self):
        with self._connect() as con:
            con.execute(
                "DELETE FROM memory_links"
            )
            con.commit()

    # ========================================================
    # Count
    # ========================================================

    def __len__(self):
        with self._connect() as con:
            row = con.execute(
                """
                SELECT COUNT(*) AS count
                FROM memory_links
                """
            ).fetchone()

        return row["count"]

# Backward-compatible alias for integrations that referred to the store as GraphStore.
GraphStore = MemoryGraphStore
