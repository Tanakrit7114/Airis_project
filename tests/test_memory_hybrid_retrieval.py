# Phase 3.7 — Hybrid Memory Retrieval

from app.memory.store import MemoryStore
from app.memory.vector_index import MemoryVectorIndex
from app.memory.hybrid_retrieval import HybridMemoryRetriever


class FakeEmbeddingModel:
    def embed(self, text):
        if not text:
            return []
        return [1.0, 0.0, 0.0]


def make_retriever():
    store = MemoryStore(db_path=":memory:")
    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    retriever = HybridMemoryRetriever(
        store=store,
        vector_index=index,
    )

    return store, index, retriever


def add_memory(store, index, key, value):
    store.add_memory(
        memory_type="preference",
        subject="user",
        key=key,
        value=value,
    )

    memory = store.get_memory_by_key(key)
    index.index_memory(memory)

    return memory


def test_hybrid_retriever_starts_empty():

    store, index, retriever = make_retriever()

    assert retriever.search("favorite language") == []


def test_hybrid_search_returns_memory():

    store, index, retriever = make_retriever()

    add_memory(
        store,
        index,
        "favorite_language",
        "Python",
    )

    results = retriever.search(
        "favorite_language"
    )

    assert len(results) == 1
    assert results[0]["value"] == "Python"


def test_hybrid_search_contains_scores():

    store, index, retriever = make_retriever()

    add_memory(
        store,
        index,
        "favorite_language",
        "Python",
    )

    results = retriever.search(
        "favorite_language"
    )

    assert len(results) == 1
    assert "similarity" in results[0]
    assert "hybrid_score" in results[0]


def test_hybrid_search_respects_limit():

    store, index, retriever = make_retriever()

    for i in range(5):
        add_memory(
            store,
            index,
            f"preference_{i}",
            f"value_{i}",
        )

    results = retriever.search(
        "preferences",
        limit=2,
    )

    assert len(results) == 2


def test_hybrid_search_exact_key_gets_high_score():

    store, index, retriever = make_retriever()

    add_memory(
        store,
        index,
        "favorite_language",
        "Python",
    )

    add_memory(
        store,
        index,
        "favorite_food",
        "Italian",
    )

    results = retriever.search(
        "favorite_language"
    )

    assert results[0]["key"] == "favorite_language"


def test_hybrid_best_returns_single_memory():

    store, index, retriever = make_retriever()

    add_memory(
        store,
        index,
        "favorite_language",
        "Python",
    )

    result = retriever.best(
        "favorite_language"
    )

    assert result is not None
    assert result["value"] == "Python"


def test_hybrid_empty_query():

    store, index, retriever = make_retriever()

    assert retriever.search("") == []


def test_hybrid_invalid_query():

    store, index, retriever = make_retriever()

    assert retriever.search(None) == []
