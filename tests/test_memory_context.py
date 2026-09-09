from app.memory.store import MemoryStore
from app.memory.context import build_context


def test_context_resolves_favorite_programming_language():
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


def test_context_resolves_favorite_color():
    store = MemoryStore(":memory:")

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_color",
        value="purple",
    )

    context = build_context(
        store,
        "What is my favorite color?",
    )

    assert "favorite_color: purple" in context


def test_context_includes_recent_conversation():
    store = MemoryStore(":memory:")

    store.add_message(
        "user",
        "Hello JARVIS",
    )

    store.add_message(
        "assistant",
        "Hello.",
    )

    context = build_context(
        store,
        "Hello",
    )

    assert "[RECENT CONVERSATION]" in context
    assert "Hello JARVIS" in context


def test_context_empty_store():
    store = MemoryStore(":memory:")

    context = build_context(
        store,
        "What is my favorite color?",
    )

    assert "[LONG-TERM MEMORY]" not in context
