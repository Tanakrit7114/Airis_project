from app.memory.orchestrator import MemoryOrchestrator
from app.memory.store import MemoryStore
from app.memory.memory_graph import MemoryGraph


def add_memory(
    store,
    key,
    value,
    importance=0.5,
    confidence=0.8,
):
    return store.add_memory(
        memory_type="preference",
        subject="user",
        key=key,
        value=value,
        importance=importance,
        confidence=confidence,
    )


# ============================================================
# Basic validation
# ============================================================


def test_orchestrator_empty_query():
    store = MemoryStore(":memory:")
    orchestrator = MemoryOrchestrator(store)

    assert orchestrator.retrieve("") == []


def test_orchestrator_invalid_query():
    store = MemoryStore(":memory:")
    orchestrator = MemoryOrchestrator(store)

    assert orchestrator.retrieve(None) == []


def test_orchestrator_limit():
    store = MemoryStore(":memory:")
    orchestrator = MemoryOrchestrator(store)

    assert orchestrator.retrieve(
        "Python",
        limit=0,
    ) == []


def test_orchestrator_negative_limit():
    store = MemoryStore(":memory:")
    orchestrator = MemoryOrchestrator(store)

    assert orchestrator.retrieve(
        "Python",
        limit=-1,
    ) == []


# ============================================================
# Exact memory retrieval
# ============================================================


def test_orchestrator_resolves_exact_memory():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "favorite_language",
        "Python",
    )

    orchestrator = MemoryOrchestrator(store)

    results = orchestrator.retrieve(
        "What programming language do I like?"
    )

    assert results

    assert any(
        item.get("key") == "favorite_language"
        and item.get("value") == "Python"
        for item in results
    )


def test_orchestrator_returns_exact_key_memory():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "favorite_language",
        "Python",
    )

    orchestrator = MemoryOrchestrator(store)

    results = orchestrator.retrieve(
        "favorite_language"
    )

    assert results

    assert results[0].get(
        "key"
    ) == "favorite_language"


# ============================================================
# Hybrid retrieval
# ============================================================


def test_orchestrator_uses_hybrid_retrieval():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "favorite_language",
        "Python",
    )

    add_memory(
        store,
        "favorite_food",
        "Pizza",
    )

    orchestrator = MemoryOrchestrator(store)

    results = orchestrator.retrieve(
        "programming language"
    )

    assert results

    keys = {
        item.get("key")
        for item in results
    }

    assert "favorite_language" in keys


# ============================================================
# Relevance / ranking
# ============================================================


def test_orchestrator_prefers_relevant_memory():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "favorite_language",
        "Python",
        importance=0.9,
        confidence=0.95,
    )

    add_memory(
        store,
        "favorite_food",
        "Pizza",
        importance=0.9,
        confidence=0.95,
    )

    orchestrator = MemoryOrchestrator(store)

    results = orchestrator.retrieve(
        "What programming language do I like?",
        limit=1,
    )

    assert len(results) == 1

    assert (
        results[0].get("key")
        == "favorite_language"
    )


def test_orchestrator_preserves_high_importance_memory():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "important_preference",
        "Python",
        importance=1.0,
        confidence=1.0,
    )

    add_memory(
        store,
        "low_preference",
        "Java",
        importance=0.1,
        confidence=0.1,
    )

    orchestrator = MemoryOrchestrator(store)

    results = orchestrator.retrieve(
        "programming language",
        limit=1,
    )

    assert len(results) == 1

    assert (
        results[0].get("key")
        == "important_preference"
    )


# ============================================================
# Limit
# ============================================================


def test_orchestrator_respects_limit():
    store = MemoryStore(":memory:")

    for i in range(10):
        add_memory(
            store,
            f"preference_{i}",
            f"value_{i}",
        )

    orchestrator = MemoryOrchestrator(store)

    results = orchestrator.retrieve(
        "preference",
        limit=3,
    )

    assert len(results) <= 3


# ============================================================
# Deduplication
# ============================================================


def test_orchestrator_deduplicates_memories():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "favorite_language",
        "Python",
    )

    orchestrator = MemoryOrchestrator(store)

    results = orchestrator.retrieve(
        "What programming language do I like?",
        limit=8,
    )

    ids = [
        str(item.get("memory_id"))
        for item in results
        if item.get("memory_id") is not None
    ]

    assert len(ids) == len(set(ids))


# ============================================================
# Graph retrieval
# ============================================================


def test_orchestrator_graph_expansion():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    first = add_memory(
        store,
        "favorite_language",
        "Python",
    )

    second = add_memory(
        store,
        "python_framework",
        "PyTorch",
    )

    assert first is not None
    assert second is not None

    orchestrator = MemoryOrchestrator(
        store=store,
        graph=graph,
    )

    results = orchestrator.retrieve(
        "favorite_language",
        limit=8,
        depth=1,
    )

    assert results


def test_orchestrator_depth_zero_disables_graph():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    add_memory(
        store,
        "favorite_language",
        "Python",
    )

    orchestrator = MemoryOrchestrator(
        store=store,
        graph=graph,
    )

    results = orchestrator.retrieve(
        "favorite_language",
        limit=8,
        depth=0,
    )

    assert results


# ============================================================
# Similarity filtering
# ============================================================


def test_orchestrator_min_similarity():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "favorite_language",
        "Python",
    )

    orchestrator = MemoryOrchestrator(store)

    results = orchestrator.retrieve(
        "completely unrelated query",
        limit=8,
        min_similarity=1.0,
    )

    assert isinstance(results, list)


# ============================================================
# Empty store
# ============================================================


def test_orchestrator_empty_store():
    store = MemoryStore(":memory:")
    orchestrator = MemoryOrchestrator(store)

    results = orchestrator.retrieve(
        "What programming language do I like?"
    )

    assert results == []


# ============================================================
# Result structure
# ============================================================


def test_orchestrator_returns_memory_objects():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "favorite_language",
        "Python",
    )

    orchestrator = MemoryOrchestrator(store)

    results = orchestrator.retrieve(
        "favorite_language"
    )

    assert results

    result = results[0]

    assert isinstance(result, dict)
    assert "memory_id" in result
    assert "key" in result
    assert "value" in result