from app.memory.store import MemoryStore
from app.memory.context import build_context


def test_context_uses_exact_memory_resolution():
    store = MemoryStore(":memory:")

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_programming_language",
        value="Python",
        importance=0.95,
        confidence=0.95,
    )

    context = build_context(
        store,
        "What is my favorite programming language?",
    )

    assert "[LONG-TERM MEMORY]" in context
    assert "favorite_programming_language: Python" in context


def test_context_uses_ranked_memory_retrieval():
    store = MemoryStore(":memory:")

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_language",
        value="Python",
        importance=0.9,
        confidence=0.9,
    )

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_food",
        value="Italian",
        importance=0.5,
        confidence=0.8,
    )

    context = build_context(
        store,
        "What programming language do I use?",
    )

    assert "Python" in context


def test_context_handles_unknown_query():
    store = MemoryStore(":memory:")

    context = build_context(
        store,
        "something completely unknown",
    )

    assert isinstance(context, str)
