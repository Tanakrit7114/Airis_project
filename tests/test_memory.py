import os
import tempfile

from app.memory.store import MemoryStore


def create_store(tmpdir):
    db_path = os.path.join(tmpdir, "test_memory.db")
    return MemoryStore(db_path), db_path


def add_test_memory(store, value="Python"):
    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_language",
        value=value,
        importance=0.9,
        confidence=1.0,
        source="test",
    )


def test_memory_add():
    with tempfile.TemporaryDirectory() as tmpdir:
        store, _ = create_store(tmpdir)

        add_test_memory(store)

        memories = store.all_memories()

        assert len(memories) == 1
        assert memories[0]["key"] == "favorite_language"
        assert memories[0]["value"] == "Python"


def test_memory_update():
    with tempfile.TemporaryDirectory() as tmpdir:
        store, _ = create_store(tmpdir)

        add_test_memory(store, "Python")
        add_test_memory(store, "Rust")

        memories = store.all_memories()

        assert len(memories) == 1
        assert memories[0]["key"] == "favorite_language"
        assert memories[0]["value"] == "Rust"


def test_memory_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        store, db_path = create_store(tmpdir)

        add_test_memory(store)

        del store

        store2 = MemoryStore(db_path)

        memories = store2.all_memories()

        assert len(memories) == 1
        assert memories[0]["key"] == "favorite_language"
        assert memories[0]["value"] == "Python"