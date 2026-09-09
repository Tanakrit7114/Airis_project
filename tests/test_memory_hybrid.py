# Phase 2.3 — Hybrid Retrieval

from app.memory.hybrid import HybridMemoryRetriever


def make_memory(
    key,
    value,
    importance=0.5,
    confidence=0.8,
    access_count=0,
    decay_rate=0.0,
):
    return {
        "memory_type": "preference",
        "subject": "user",
        "key": key,
        "value": value,
        "importance": importance,
        "confidence": confidence,
        "access_count": access_count,
        "decay_rate": decay_rate,
    }


def test_hybrid_returns_list():
    retriever = HybridMemoryRetriever()

    memories = [
        make_memory(
            "favorite_language",
            "Python",
        )
    ]

    result = retriever.retrieve(
        "programming language",
        memories,
    )

    assert isinstance(result, list)


def test_hybrid_finds_exact_value():
    retriever = HybridMemoryRetriever()

    memories = [
        make_memory(
            "favorite_language",
            "Python",
        ),
        make_memory(
            "favorite_food",
            "Italian",
        ),
    ]

    result = retriever.retrieve(
        "Python",
        memories,
    )

    assert result[0]["key"] == "favorite_language"


def test_hybrid_finds_related_key():
    retriever = HybridMemoryRetriever()

    memories = [
        make_memory(
            "favorite_language",
            "Python",
        ),
        make_memory(
            "favorite_food",
            "Italian",
        ),
    ]

    result = retriever.retrieve(
        "language",
        memories,
    )

    assert result[0]["key"] == "favorite_language"


def test_hybrid_combines_relevance_and_ranking():
    retriever = HybridMemoryRetriever()

    memories = [
        make_memory(
            "memory_a",
            "Python",
            importance=0.2,
        ),
        make_memory(
            "memory_b",
            "Python",
            importance=0.9,
        ),
    ]

    result = retriever.retrieve(
        "Python",
        memories,
    )

    assert result[0]["key"] == "memory_b"


def test_hybrid_respects_limit():
    retriever = HybridMemoryRetriever()

    memories = [
        make_memory(
            f"memory_{i}",
            "Python",
        )
        for i in range(10)
    ]

    result = retriever.retrieve(
        "Python",
        memories,
        limit=3,
    )

    assert len(result) == 3


def test_hybrid_empty_query():
    retriever = HybridMemoryRetriever()

    memories = [
        make_memory(
            "favorite_language",
            "Python",
        )
    ]

    assert retriever.retrieve(
        "",
        memories,
    ) == []


def test_hybrid_empty_memories():
    retriever = HybridMemoryRetriever()

    assert retriever.retrieve(
        "Python",
        [],
    ) == []


def test_hybrid_preserves_memory_data():
    retriever = HybridMemoryRetriever()

    memory = make_memory(
        "favorite_language",
        "Python",
    )

    result = retriever.retrieve(
        "Python",
        [memory],
    )

    assert result[0]["key"] == "favorite_language"
    assert result[0]["value"] == "Python"


def test_hybrid_adds_score():
    retriever = HybridMemoryRetriever()

    memories = [
        make_memory(
            "favorite_language",
            "Python",
        )
    ]

    result = retriever.retrieve(
        "Python",
        memories,
    )

    assert "ranking_score" in result[0]


def test_hybrid_decay_affects_result():
    retriever = HybridMemoryRetriever()

    memories = [
        make_memory(
            "memory_a",
            "Python",
            decay_rate=0.9,
        ),
        make_memory(
            "memory_b",
            "Python",
            decay_rate=0.0,
        ),
    ]

    result = retriever.retrieve(
        "Python",
        memories,
    )

    assert result[0]["key"] == "memory_b"
