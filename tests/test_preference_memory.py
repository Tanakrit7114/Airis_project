from app.memory.extractor import MemoryExtractor
from app.memory.store import MemoryStore


def test_extract_favorite_programming_language():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "My favorite programming language is Python"
    )

    assert len(result) == 1

    memory = result[0]

    assert memory["memory_type"] == "preference"
    assert memory["subject"] == "user"
    assert memory["key"] == "favorite_programming_language"
    assert memory["value"] == "Python"
    assert memory["importance"] >= 0.9
    assert memory["confidence"] >= 0.9


def test_extract_favorite_color():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "My favorite color is purple"
    )

    assert len(result) == 1

    memory = result[0]

    assert memory["memory_type"] == "preference"
    assert memory["key"] == "favorite_color"
    assert memory["value"].lower() == "purple"


def test_extract_like_preference():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "I like blue"
    )

    assert len(result) == 1

    memory = result[0]

    assert memory["memory_type"] == "preference"
    assert memory["key"] == "favorite_color"
    assert memory["value"] == "blue"


def test_store_preference():
    store = MemoryStore(":memory:")

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_programming_language",
        value="Python",
        importance=0.95,
        confidence=0.95,
    )

    memory = store.get_memory_by_key(
        "favorite_programming_language"
    )

    assert memory is not None
    assert memory["memory_type"] == "preference"
    assert memory["value"] == "Python"


def test_update_preference():
    store = MemoryStore(":memory:")

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_programming_language",
        value="Python",
    )

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_programming_language",
        value="Rust",
    )

    memory = store.get_memory_by_key(
        "favorite_programming_language"
    )

    assert memory["value"] == "Rust"


def test_retrieve_preference():
    store = MemoryStore(":memory:")

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_programming_language",
        value="Python",
    )

    results = store.retrieve(
        "favorite programming language",
        limit=5,
    )

    assert len(results) >= 1
    assert any(
        result["value"] == "Python"
        for result in results
    )
