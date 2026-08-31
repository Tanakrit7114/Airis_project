from app.memory.store import MemoryStore
from app.memory.context import build_context


def test_context_assembly_empty_query():
    store = MemoryStore(":memory:")

    assert build_context(
        store,
        "",
    ) == ""


def test_context_assembly_invalid_query():
    store = MemoryStore(":memory:")

    assert build_context(
        store,
        None,
    ) == ""


def test_context_assembly_contains_memory():
    store = MemoryStore(":memory:")

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_language",
        value="Python",
        importance=0.9,
        confidence=0.95,
    )

    context = build_context(
        store,
        "What programming language do I like?",
    )

    assert "[LONG-TERM MEMORY]" in context
    assert "favorite_language: Python" in context


def test_context_assembly_contains_recent_conversation():
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
    assert "[user] Hello JARVIS" in context
    assert "[assistant] Hello." in context


def test_context_assembly_sections_are_separated():
    store = MemoryStore(":memory:")

    store.add_memory(
        memory_type="preference",
        subject="user",
        key="favorite_language",
        value="Python",
    )

    store.add_message(
        "user",
        "Hello JARVIS",
    )

    context = build_context(
        store,
        "What programming language do I like?",
    )

    assert "[LONG-TERM MEMORY]" in context
    assert "[RECENT CONVERSATION]" in context

    memory_pos = context.index(
        "[LONG-TERM MEMORY]"
    )

    conversation_pos = context.index(
        "[RECENT CONVERSATION]"
    )

    assert memory_pos < conversation_pos


def test_context_assembly_respects_memory_limit():
    store = MemoryStore(":memory:")

    for i in range(10):
        store.add_memory(
            memory_type="preference",
            subject="user",
            key=f"preference_{i}",
            value=f"value_{i}",
        )

    context = build_context(
        store,
        "preference",
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
