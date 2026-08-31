from app.memory.context_builder import (
    MemoryContextBuilder,
)


def test_context_builder_empty_memory():

    builder = MemoryContextBuilder()

    assert builder.build([]) == ""


def test_context_builder_none():

    builder = MemoryContextBuilder()

    assert builder.build(None) == ""


def test_context_builder_single_memory():

    builder = MemoryContextBuilder()

    memories = [
        {
            "memory_id": "1",
            "key": "favorite_language",
            "value": "Python",
            "importance": 0.9,
            "confidence": 0.95,
        }
    ]

    context = builder.build(memories)

    assert context

    assert "favorite_language: Python" in context


def test_context_builder_preserves_importance():

    builder = MemoryContextBuilder()

    memories = [
        {
            "memory_id": "1",
            "key": "favorite_language",
            "value": "Python",
            "importance": 1.0,
            "confidence": 1.0,
        }
    ]

    context = builder.build(memories)

    assert "importance=1.00" in context
    assert "confidence=1.00" in context


def test_context_builder_orders_by_relevance():

    builder = MemoryContextBuilder()

    memories = [
        {
            "memory_id": "1",
            "key": "food",
            "value": "Pizza",
            "relevance_score": 0.2,
            "importance": 0.9,
            "confidence": 0.9,
        },
        {
            "memory_id": "2",
            "key": "language",
            "value": "Python",
            "relevance_score": 0.9,
            "importance": 0.9,
            "confidence": 0.9,
        },
    ]

    context = builder.build(memories)

    python_position = context.index(
        "language: Python"
    )

    pizza_position = context.index(
        "food: Pizza"
    )

    assert python_position < pizza_position


def test_context_builder_deduplicates():

    builder = MemoryContextBuilder()

    memories = [
        {
            "memory_id": "1",
            "key": "favorite_language",
            "value": "Python",
        },
        {
            "memory_id": "1",
            "key": "favorite_language",
            "value": "Python",
        },
    ]

    context = builder.build(memories)

    assert context.count(
        "favorite_language: Python"
    ) == 1


def test_context_builder_respects_limit():

    builder = MemoryContextBuilder()

    memories = []

    for i in range(10):
        memories.append(
            {
                "memory_id": str(i),
                "key": f"preference_{i}",
                "value": f"value_{i}",
                "relevance_score": 1.0 - i * 0.01,
            }
        )

    context = builder.build(
        memories,
        limit=3,
    )

    assert context.count("- ") == 3


def test_context_builder_uses_content():

    builder = MemoryContextBuilder()

    memories = [
        {
            "memory_id": "1",
            "key": "favorite_language",
            "value": "Python",
            "content": "The user prefers Python",
        }
    ]

    context = builder.build(memories)

    assert "The user prefers Python" in context