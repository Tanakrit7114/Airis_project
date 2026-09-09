# Phase 3.6 — Semantic Memory Retrieval

from app.memory.store import MemoryStore
from app.memory.vector_index import MemoryVectorIndex
from app.memory.semantic_retrieval import (
    SemanticMemoryRetriever,
)


class FakeEmbeddingModel:

    def embed(self, text):
        if not text:
            return []

        return [1.0, 0.0, 0.0]


def test_semantic_retriever_starts_empty():

    store = MemoryStore(
        db_path=":memory:"
    )

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    retriever = SemanticMemoryRetriever(
        store=store,
        vector_index=index,
    )

    assert retriever.search(
        "favorite language"
    ) == []


def test_semantic_search_returns_memory():

    store = MemoryStore(
        db_path=":memory:"
    )

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    retriever = SemanticMemoryRetriever(
        store=store,
        vector_index=index,
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

    index.index_memory(
        memory
    )

    results = retriever.search(
        "What programming language do I like?"
    )

    assert len(results) == 1
    assert results[0]["value"] == "Python"


def test_semantic_search_contains_similarity():

    store = MemoryStore(
        db_path=":memory:"
    )

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    retriever = SemanticMemoryRetriever(
        store=store,
        vector_index=index,
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

    index.index_memory(
        memory
    )

    results = retriever.search(
        "programming language"
    )

    assert "similarity" in results[0]
    assert results[0]["similarity"] > 0


def test_semantic_search_respects_limit():

    store = MemoryStore(
        db_path=":memory:"
    )

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    retriever = SemanticMemoryRetriever(
        store=store,
        vector_index=index,
    )

    for i in range(5):

        store.add_memory(
            memory_type="preference",
            subject="user",
            key=f"preference_{i}",
            value=f"value_{i}",
        )

        memory = store.get_memory_by_key(
            f"preference_{i}"
        )

        index.index_memory(
            memory
        )

    results = retriever.search(
        "preferences",
        limit=2,
    )

    assert len(results) == 2


def test_semantic_search_empty_query():

    store = MemoryStore(
        db_path=":memory:"
    )

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    retriever = SemanticMemoryRetriever(
        store=store,
        vector_index=index,
    )

    assert retriever.search("") == []


def test_best_returns_single_memory():

    store = MemoryStore(
        db_path=":memory:"
    )

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    retriever = SemanticMemoryRetriever(
        store=store,
        vector_index=index,
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

    index.index_memory(
        memory
    )

    result = retriever.best(
        "What language do I like?"
    )

    assert result is not None
    assert result["value"] == "Python"
