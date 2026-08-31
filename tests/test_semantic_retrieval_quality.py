from app.memory.semantic_retrieval import SemanticMemoryRetriever
from app.memory.store import MemoryStore


class FakeVectorIndex:
    def __init__(self, results):
        self.results = results

    def search(self, query, limit=5):
        return self.results[:limit]


def add_memory(
    store,
    key,
    value,
    importance=0.8,
    confidence=0.9,
):
    return store.add_memory(
        memory_type="preference",
        subject="user",
        key=key,
        value=value,
        importance=importance,
        confidence=confidence,
    )


def test_semantic_retrieval_filters_low_similarity():
    store = MemoryStore(":memory:")

    memory_id = add_memory(
        store,
        "favorite_programming_language",
        "Python",
        importance=1.0,
        confidence=1.0,
    )

    retriever = SemanticMemoryRetriever(
        store=store,
        vector_index=FakeVectorIndex(
            [
                {
                    "memory_id": memory_id,
                    "similarity": 0.90,
                }
            ]
        ),
    )

    results = retriever.search(
        "What programming language do I like?",
        min_similarity=0.80,
    )

    assert len(results) == 1
    assert results[0]["key"] == "favorite_programming_language"
    assert results[0]["value"] == "Python"


def test_semantic_retrieval_rejects_low_similarity():
    store = MemoryStore(":memory:")

    memory_id = add_memory(
        store,
        "favorite_food",
        "Pizza",
        importance=1.0,
        confidence=1.0,
    )

    retriever = SemanticMemoryRetriever(
        store=store,
        vector_index=FakeVectorIndex(
            [
                {
                    "memory_id": memory_id,
                    "similarity": 0.20,
                }
            ]
        ),
    )

    results = retriever.search(
        "What programming language do I like?",
        min_similarity=0.80,
    )

    assert results == []


def test_semantic_retrieval_preserves_high_similarity_order():
    store = MemoryStore(":memory:")

    programming_id = add_memory(
        store,
        "favorite_programming_language",
        "Python",
        importance=1.0,
        confidence=1.0,
    )

    food_id = add_memory(
        store,
        "favorite_food",
        "Pizza",
        importance=1.0,
        confidence=1.0,
    )

    retriever = SemanticMemoryRetriever(
        store=store,
        vector_index=FakeVectorIndex(
            [
                {
                    "memory_id": programming_id,
                    "similarity": 0.95,
                },
                {
                    "memory_id": food_id,
                    "similarity": 0.60,
                },
            ]
        ),
    )

    results = retriever.search(
        "programming language",
        min_similarity=0.50,
    )

    assert len(results) == 2
    assert results[0]["key"] == "favorite_programming_language"
    assert results[1]["key"] == "favorite_food"
