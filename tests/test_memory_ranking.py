# Phase 2.2 — Memory Ranking
# tests/test_memory_ranking.py

from app.memory.ranking import MemoryRanker


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


def test_rank_returns_list():
    ranker = MemoryRanker()

    memories = [
        make_memory(
            "favorite_language",
            "Python",
        )
    ]

    result = ranker.rank(
        "language",
        memories,
    )

    assert isinstance(result, list)


def test_rank_keeps_memory_data():
    ranker = MemoryRanker()

    memory = make_memory(
        "favorite_language",
        "Python",
    )

    result = ranker.rank(
        "language",
        [memory],
    )

    assert result[0]["key"] == "favorite_language"
    assert result[0]["value"] == "Python"


def test_relevant_memory_ranks_higher():
    ranker = MemoryRanker()

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

    result = ranker.rank(
        "programming language",
        memories,
    )

    assert result[0]["key"] == "favorite_language"


def test_importance_affects_ranking():
    ranker = MemoryRanker()

    memories = [
        make_memory(
            "memory_a",
            "Python",
            importance=0.9,
        ),
        make_memory(
            "memory_b",
            "Python",
            importance=0.2,
        ),
    ]

    result = ranker.rank(
        "Python",
        memories,
    )

    assert result[0]["key"] == "memory_a"


def test_confidence_affects_ranking():
    ranker = MemoryRanker()

    memories = [
        make_memory(
            "memory_a",
            "Python",
            confidence=0.95,
        ),
        make_memory(
            "memory_b",
            "Python",
            confidence=0.30,
        ),
    ]

    result = ranker.rank(
        "Python",
        memories,
    )

    assert result[0]["key"] == "memory_a"


def test_access_count_affects_ranking():
    ranker = MemoryRanker()

    memories = [
        make_memory(
            "memory_a",
            "Python",
            access_count=20,
        ),
        make_memory(
            "memory_b",
            "Python",
            access_count=1,
        ),
    ]

    result = ranker.rank(
        "Python",
        memories,
    )

    assert result[0]["key"] == "memory_a"


def test_decay_reduces_ranking():
    ranker = MemoryRanker()

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

    result = ranker.rank(
        "Python",
        memories,
    )

    assert result[0]["key"] == "memory_b"


def test_rank_limit():
    ranker = MemoryRanker()

    memories = [
        make_memory(
            f"memory_{i}",
            "Python",
        )
        for i in range(10)
    ]

    result = ranker.rank(
        "Python",
        memories,
        limit=3,
    )

    assert len(result) == 3


def test_empty_query():
    ranker = MemoryRanker()

    memories = [
        make_memory(
            "favorite_language",
            "Python",
        )
    ]

    assert ranker.rank(
        "",
        memories,
    ) == []


def test_empty_memories():
    ranker = MemoryRanker()

    assert ranker.rank(
        "Python",
        [],
    ) == []
