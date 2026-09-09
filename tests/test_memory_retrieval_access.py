from app.memory.store import MemoryStore


def test_retrieve_updates_access_count(tmp_path):
    store = MemoryStore(
        db_path=str(tmp_path / "memory.db")
    )

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_language",
        value="Python",
    )

    memory = store.get_memory_by_key(
        "favorite_language"
    )

    assert memory["access_count"] == 0

    results = store.retrieve(
        "Python",
        limit=5,
    )

    assert len(results) == 1

    updated = store.get_memory(
        memory["memory_id"]
    )

    assert updated["access_count"] == 1


def test_retrieve_updates_last_accessed(tmp_path):
    store = MemoryStore(
        db_path=str(tmp_path / "memory.db")
    )

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_language",
        value="Python",
    )

    memory = store.get_memory_by_key(
        "favorite_language"
    )

    assert memory["last_accessed"] is None

    store.retrieve(
        "Python",
        limit=5,
    )

    updated = store.get_memory(
        memory["memory_id"]
    )

    assert updated["last_accessed"] is not None


def test_repeated_retrieval_increases_access_count(tmp_path):
    store = MemoryStore(
        db_path=str(tmp_path / "memory.db")
    )

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_language",
        value="Python",
    )

    memory = store.get_memory_by_key(
        "favorite_language"
    )

    memory_id = memory["memory_id"]

    store.retrieve("Python")
    store.retrieve("Python")
    store.retrieve("Python")

    updated = store.get_memory(memory_id)

    assert updated["access_count"] == 3
