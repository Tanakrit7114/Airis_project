from app.memory.store import MemoryStore


def test_access_count_starts_at_zero(tmp_path):
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


def test_access_memory_increments_count(tmp_path):
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

    store.access_memory(
        memory["memory_id"]
    )

    updated = store.get_memory(
        memory["memory_id"]
    )

    assert updated["access_count"] == 1


def test_access_memory_updates_last_accessed(tmp_path):
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

    store.access_memory(
        memory["memory_id"]
    )

    updated = store.get_memory(
        memory["memory_id"]
    )

    assert updated["last_accessed"] is not None


def test_multiple_accesses_increment_count(tmp_path):
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

    store.access_memory(memory_id)
    store.access_memory(memory_id)
    store.access_memory(memory_id)

    updated = store.get_memory(memory_id)

    assert updated["access_count"] == 3
