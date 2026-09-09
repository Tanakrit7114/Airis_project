from app.memory.store import MemoryStore
from app.memory.context import build_context


def add_memory(
    store,
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


def test_context_intelligence_prefers_relevant_memory():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "favorite_language",
        "Python",
        importance=0.9,
        confidence=0.95,
    )

    add_memory(
        store,
        "favorite_food",
        "Pizza",
        importance=0.9,
        confidence=0.95,
    )

    context = build_context(
        store,
        "What programming language do I like?",
        limit=1,
    )

    assert "favorite_language: Python" in context
    assert "favorite_food: Pizza" not in context


def test_context_intelligence_respects_limit():
    store = MemoryStore(":memory:")

    for i in range(10):
        add_memory(
            store,
            f"preference_{i}",
            f"value_{i}",
        )

    context = build_context(
        store,
        "preferences",
        limit=3,
    )

    memory_section = context.split(
        "[RECENT CONVERSATION]"
    )[0]

    memory_lines = [
        line
        for line in memory_section.splitlines()
        if line.startswith("- ")
    ]

    assert len(memory_lines) <= 3


def test_context_intelligence_preserves_high_importance_memory():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "important_preference",
        "Python",
        importance=1.0,
        confidence=1.0,
    )

    add_memory(
        store,
        "low_preference",
        "Java",
        importance=0.1,
        confidence=0.1,
    )

    context = build_context(
        store,
        "programming language",
        limit=1,
    )

    assert "important_preference: Python" in context
    assert "low_preference: Java" not in context


def test_context_intelligence_keeps_recent_conversation():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "favorite_language",
        "Python",
    )

    store.add_message(
        "user",
        "I am working on JARVIS.",
    )

    context = build_context(
        store,
        "What programming language do I like?",
        limit=1,
    )

    assert "[LONG-TERM MEMORY]" in context
    assert "[RECENT CONVERSATION]" in context
    assert "I am working on JARVIS." in context


def test_context_intelligence_empty_query():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "favorite_language",
        "Python",
    )

    assert build_context(
        store,
        "",
    ) == ""


def test_context_intelligence_no_irrelevant_memory():
    store = MemoryStore(":memory:")

    add_memory(
        store,
        "favorite_food",
        "Pizza",
        importance=1.0,
        confidence=1.0,
    )

    context = build_context(
        store,
        "What programming language do I like?",
        limit=1,
    )

    assert "favorite_food: Pizza" not in context
