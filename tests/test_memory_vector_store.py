# Phase 3.3 — Memory Vector Store

from app.memory.vector_store import MemoryVectorStore


def test_vector_store_starts_empty():

    store = MemoryVectorStore()

    assert len(store) == 0


def test_add_vector():

    store = MemoryVectorStore()

    result = store.add(
        "memory_1",
        [1.0, 0.0, 0.0],
    )

    assert result is True
    assert len(store) == 1


def test_get_vector():

    store = MemoryVectorStore()

    store.add(
        "memory_1",
        [1.0, 0.0, 0.0],
    )

    vector = store.get("memory_1")

    assert vector == [
        1.0,
        0.0,
        0.0,
    ]


def test_get_missing_vector():

    store = MemoryVectorStore()

    assert store.get("missing") is None


def test_replace_vector():

    store = MemoryVectorStore()

    store.add(
        "memory_1",
        [1.0, 0.0, 0.0],
    )

    store.add(
        "memory_1",
        [0.0, 1.0, 0.0],
    )

    assert store.get("memory_1") == [
        0.0,
        1.0,
        0.0,
    ]

    assert len(store) == 1


def test_delete_vector():

    store = MemoryVectorStore()

    store.add(
        "memory_1",
        [1.0, 0.0, 0.0],
    )

    result = store.delete("memory_1")

    assert result is True
    assert len(store) == 0
    assert store.get("memory_1") is None


def test_delete_missing_vector():

    store = MemoryVectorStore()

    assert store.delete("missing") is False


def test_clear():

    store = MemoryVectorStore()

    store.add(
        "memory_1",
        [1.0, 0.0, 0.0],
    )

    store.add(
        "memory_2",
        [0.0, 1.0, 0.0],
    )

    store.clear()

    assert len(store) == 0


def test_search_returns_most_similar():

    store = MemoryVectorStore()

    store.add(
        "python",
        [1.0, 0.0, 0.0],
    )

    store.add(
        "italian",
        [0.0, 1.0, 0.0],
    )

    result = store.search(
        [0.9, 0.1, 0.0],
        limit=2,
    )

    assert result[0]["memory_id"] == "python"
    assert result[0]["similarity"] > result[1]["similarity"]


def test_search_respects_limit():

    store = MemoryVectorStore()

    for i in range(10):

        store.add(
            f"memory_{i}",
            [1.0, 0.0, 0.0],
        )

    result = store.search(
        [1.0, 0.0, 0.0],
        limit=3,
    )

    assert len(result) == 3


def test_search_empty():

    store = MemoryVectorStore()

    assert store.search(
        [1.0, 0.0, 0.0],
    ) == []


def test_search_zero_vector():

    store = MemoryVectorStore()

    store.add(
        "memory_1",
        [1.0, 0.0, 0.0],
    )

    result = store.search(
        [0.0, 0.0, 0.0],
    )

    assert result[0]["similarity"] == 0.0


def test_dimension_mismatch():

    store = MemoryVectorStore()

    store.add(
        "memory_1",
        [1.0, 0.0, 0.0],
    )

    result = store.search(
        [1.0, 0.0],
    )

    assert result[0]["similarity"] == 0.0
