from app.memory.pipeline import MemoryPipeline
from app.memory.store import MemoryStore


def test_pipeline_store_memory(tmp_path):

    db_path = tmp_path / "memory.db"

    store = MemoryStore(
        db_path=str(db_path)
    )

    pipeline = MemoryPipeline(
        store=store
    )

    result = pipeline.process(
        "I prefer Python."
    )

    assert len(result) == 1

    stored = pipeline.store_memories(
        result
    )

    assert len(stored) == 1

    memories = store.all_memories_v2()

    assert len(memories) == 1

    memory = memories[0]

    assert memory["memory_type"] == "preference"
    assert memory["subject"] == "user"
    assert memory["key"] == "favorite_language"
    assert memory["value"] == "Python"
    assert memory["content"] == "favorite_language: Python"
