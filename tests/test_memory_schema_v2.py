import sqlite3

from app.memory.store import MemoryStore


def test_memory_schema_v2(tmp_path):

    db_path = tmp_path / "memory.db"

    store = MemoryStore(db_path)

    with sqlite3.connect(db_path) as con:

        columns = {
            row[1]
            for row in con.execute(
                "PRAGMA table_info(memories)"
            ).fetchall()
        }

    required = {
        "memory_id",
        "memory_type",
        "subject",
        "key",
        "value",
        "content",
        "importance",
        "confidence",
        "source",
        "tags",
        "entities",
        "relationships",
        "created_at",
        "updated_at",
        "last_accessed",
        "access_count",
        "decay_rate",
        "expires_at",
    }

    assert required.issubset(columns)


def test_memory_v2_defaults(tmp_path):

    db_path = tmp_path / "memory.db"

    store = MemoryStore(db_path)

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_language",
        value="Python",
    )

    memories = store.all_memories_v2()

    assert len(memories) == 1

    memory = memories[0]

    assert memory["memory_id"]
    assert memory["content"] == "favorite_language: Python"

    assert memory["tags"] == []
    assert memory["entities"] == []
    assert memory["relationships"] == []

    assert memory["access_count"] == 0
    assert memory["decay_rate"] == 0.0
