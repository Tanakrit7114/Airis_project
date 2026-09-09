# Phase 2.1 — Memory Retrieval Tests

from app.memory.store import MemoryStore
from app.memory.retrieval import MemoryRetriever


def make_store(tmp_path):
    return MemoryStore(
        db_path=str(
            tmp_path / "memory.db"
        )
    )


def test_retrieve_relevant_memory(tmp_path):
    store = make_store(tmp_path)

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_language",
        value="Python",
    )

    retriever = MemoryRetriever(store)

    result = retriever.retrieve(
        "favorite language"
    )

    assert len(result) == 1
    assert result[0]["value"] == "Python"


def test_retrieve_respects_limit(tmp_path):
    store = make_store(tmp_path)

    store.add_memory(
        "preference",
        "user",
        "favorite_language",
        "Python",
    )

    store.add_memory(
        "preference",
        "user",
        "favorite_food",
        "Italian",
    )

    retriever = MemoryRetriever(store)

    result = retriever.retrieve(
        "favorite",
        limit=1,
    )

    assert len(result) == 1


def test_retrieve_empty_query(tmp_path):
    store = make_store(tmp_path)

    retriever = MemoryRetriever(store)

    assert retriever.retrieve("") == []


def test_retrieve_invalid_query(tmp_path):
    store = make_store(tmp_path)

    retriever = MemoryRetriever(store)

    assert retriever.retrieve(None) == []


def test_retrieve_zero_limit(tmp_path):
    store = make_store(tmp_path)

    retriever = MemoryRetriever(store)

    assert retriever.retrieve(
        "Python",
        limit=0,
    ) == []


def test_retrieve_negative_limit(tmp_path):
    store = make_store(tmp_path)

    retriever = MemoryRetriever(store)

    assert retriever.retrieve(
        "Python",
        limit=-1,
    ) == []


def test_retrieve_one_returns_memory(tmp_path):
    store = make_store(tmp_path)

    store.add_memory(
        "preference",
        "user",
        "favorite_language",
        "Python",
    )

    retriever = MemoryRetriever(store)

    result = retriever.retrieve_one(
        "Python"
    )

    assert result is not None
    assert result["value"] == "Python"


def test_retrieve_one_returns_none(tmp_path):
    store = make_store(tmp_path)

    retriever = MemoryRetriever(store)

    result = retriever.retrieve_one(
        "something_unknown"
    )

    assert result is None
