from app.memory.store import MemoryStore
from app.memory.consolidator import MemoryConsolidator


def add_memory(
    store,
    key,
    value,
    memory_type="preference",
    subject="user",
    tags=None,
    entities=None,
    importance=0.8,
    confidence=0.9,
):
    return store.add_memory(
        memory_type=memory_type,
        subject=subject,
        key=key,
        value=value,
        tags=tags or [],
        entities=entities or [],
        importance=importance,
        confidence=confidence,
    )


def test_consolidator_exists():
    store = MemoryStore(":memory:")

    consolidator = MemoryConsolidator(store)

    assert consolidator is not None


def test_consolidate_related_memories():
    store = MemoryStore(":memory:")

    first_id = add_memory(
        store,
        "favorite_language",
        "Python",
        tags=["programming", "ai"],
        entities=["Python", "AI"],
    )

    second_id = add_memory(
        store,
        "python_framework",
        "PyTorch",
        tags=["programming", "ai"],
        entities=["Python", "AI", "PyTorch"],
    )

    consolidator = MemoryConsolidator(store)

    result = consolidator.consolidate(
        [first_id, second_id]
    )

    assert result is not None


def test_consolidated_memory_contains_source_information():
    store = MemoryStore(":memory:")

    first_id = add_memory(
        store,
        "favorite_language",
        "Python",
        tags=["programming"],
        entities=["Python"],
    )

    second_id = add_memory(
        store,
        "python_framework",
        "PyTorch",
        tags=["programming", "ai"],
        entities=["Python", "PyTorch"],
    )

    consolidator = MemoryConsolidator(store)

    result = consolidator.consolidate(
        [first_id, second_id]
    )

    assert result is not None

    memory = store.get_memory(result)

    assert memory is not None
    assert "Python" in memory["content"]
    assert "PyTorch" in memory["content"]


def test_consolidation_merges_tags():
    store = MemoryStore(":memory:")

    first_id = add_memory(
        store,
        "python_interest",
        "Python",
        tags=["programming", "language"],
    )

    second_id = add_memory(
        store,
        "ai_interest",
        "AI",
        tags=["programming", "ai"],
    )

    consolidator = MemoryConsolidator(store)

    result = consolidator.consolidate(
        [first_id, second_id]
    )

    memory = store.get_memory(result)

    assert "programming" in memory["tags"]
    assert "language" in memory["tags"]
    assert "ai" in memory["tags"]


def test_consolidation_merges_entities():
    store = MemoryStore(":memory:")

    first_id = add_memory(
        store,
        "python",
        "Python",
        entities=["Python"],
    )

    second_id = add_memory(
        store,
        "pytorch",
        "PyTorch",
        entities=["Python", "PyTorch"],
    )

    consolidator = MemoryConsolidator(store)

    result = consolidator.consolidate(
        [first_id, second_id]
    )

    memory = store.get_memory(result)

    assert "Python" in memory["entities"]
    assert "PyTorch" in memory["entities"]


def test_consolidation_requires_multiple_memories():
    store = MemoryStore(":memory:")

    memory_id = add_memory(
        store,
        "favorite_language",
        "Python",
    )

    consolidator = MemoryConsolidator(store)

    result = consolidator.consolidate(
        [memory_id]
    )

    assert result is None


def test_consolidation_rejects_invalid_ids():
    store = MemoryStore(":memory:")

    consolidator = MemoryConsolidator(store)

    assert consolidator.consolidate([]) is None
    assert consolidator.consolidate(None) is None
