# Phase 3.8 — Memory Relevance / Reranking

from app.memory.store import MemoryStore
from app.memory.vector_index import MemoryVectorIndex
from app.memory.hybrid_retrieval import HybridMemoryRetriever


class FakeEmbeddingModel:
    def embed(self, text):
        if not text:
            return []

        text = text.lower()

        if "language" in text or "python" in text:
            return [1.0, 0.0, 0.0]

        if "food" in text or "pizza" in text:
            return [0.0, 1.0, 0.0]

        return [0.5, 0.5, 0.0]


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


def add_memory(
    store,
    index,
    key,
    value,
    importance=0.5,
    confidence=0.8,
):
    store.add_memory(
        memory_type="preference",
        subject="user",
        key=key,
        value=value,
        importance=importance,
        confidence=confidence,
    )

    memory = store.get_memory_by_key(key)
    index.index_memory(memory)

    return memory


def test_reranking_returns_relevance_score():
    store, index, retriever = make_retriever()

    add_memory(
        store,
        index,
        "favorite_language",
        "Python",
    )

    results = retriever.rerank(
        "What programming language do I like?"
    )

    assert len(results) == 1
    assert "relevance_score" in results[0]
    assert results[0]["relevance_score"] > 0


def test_reranking_prefers_exact_relevant_memory():
    store, index, retriever = make_retriever()

    add_memory(
        store,
        index,
        "favorite_language",
        "Python",
        importance=0.9,
        confidence=0.95,
    )

    add_memory(
        store,
        index,
        "favorite_food",
        "Pizza",
        importance=0.5,
        confidence=0.8,
    )

    results = retriever.rerank(
        "What programming language do I like?"
    )

    assert results
    assert results[0]["key"] == "favorite_language"
    assert results[0]["value"] == "Python"


def test_reranking_respects_limit():
    store, index, retriever = make_retriever()

    for i in range(5):
        add_memory(
            store,
            index,
            f"favorite_language_{i}",
            "Python",
        )

    results = retriever.rerank(
        "programming language",
        limit=2,
    )

    assert len(results) == 2


def test_reranking_preserves_hybrid_scores():
    store, index, retriever = make_retriever()

    add_memory(
        store,
        index,
        "favorite_language",
        "Python",
    )

    results = retriever.rerank(
        "programming language"
    )

    assert "similarity" in results[0]
    assert "exact_score" in results[0]
    assert "hybrid_score" in results[0]
    assert "relevance_score" in results[0]


def test_reranking_uses_importance_and_confidence():
    store, index, retriever = make_retriever()

    add_memory(
        store,
        index,
        "language_a",
        "Python",
        importance=1.0,
        confidence=1.0,
    )

    add_memory(
        store,
        index,
        "language_b",
        "Python",
        importance=0.1,
        confidence=0.1,
    )

    results = retriever.rerank(
        "programming language"
    )

    assert results[0]["key"] == "language_a"


def test_reranking_empty_query():
    store, index, retriever = make_retriever()

    add_memory(
        store,
        index,
        "favorite_language",
        "Python",
    )

    assert retriever.rerank("") == []


def test_reranking_invalid_limit():
    store, index, retriever = make_retriever()

    add_memory(
        store,
        index,
        "favorite_language",
        "Python",
    )

    assert retriever.rerank(
        "programming language",
        limit=0,
    ) == []


def test_best_reranked_returns_single_memory():
    store, index, retriever = make_retriever()

    add_memory(
        store,
        index,
        "favorite_language",
        "Python",
        importance=0.9,
        confidence=0.95,
    )

    result = retriever.best_reranked(
        "What language do I like?"
    )

    assert result is not None
    assert result["key"] == "favorite_language"
    assert result["value"] == "Python"
    assert "relevance_score" in result
