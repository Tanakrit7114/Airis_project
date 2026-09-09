from app.memory.consolidation import MemoryConsolidator


def make_memory(
    memory_type="preference",
    subject="user",
    key="favorite_language",
    value="Python",
    importance=0.5,
):
    return {
        "memory_type": memory_type,
        "subject": subject,
        "key": key,
        "value": value,
        "importance": importance,
    }


def test_same_memory_signature_is_related():
    consolidator = MemoryConsolidator()

    a = make_memory(value="Python")
    b = make_memory(value="Rust")

    assert consolidator.are_related(a, b)


def test_different_key_is_not_related():
    consolidator = MemoryConsolidator()

    a = make_memory(
        key="favorite_language",
        value="Python",
    )

    b = make_memory(
        key="favorite_color",
        value="Blue",
    )

    assert not consolidator.are_related(a, b)


def test_different_subject_is_not_related():
    consolidator = MemoryConsolidator()

    a = make_memory(
        subject="user",
        value="Python",
    )

    b = make_memory(
        subject="project",
        value="Python",
    )

    assert not consolidator.are_related(a, b)


def test_consolidate_groups_related_memories():
    consolidator = MemoryConsolidator()

    memories = [
        make_memory(value="Python"),
        make_memory(value="Rust"),
        make_memory(
            key="favorite_color",
            value="Blue",
        ),
    ]

    groups = consolidator.consolidate(memories)

    assert len(groups) == 2
    assert len(groups[0]) == 2
    assert len(groups[1]) == 1


def test_consolidate_empty():
    consolidator = MemoryConsolidator()

    assert consolidator.consolidate([]) == []


def test_merge_single_memory():
    consolidator = MemoryConsolidator()

    memory = make_memory(
        value="Python",
        importance=0.9,
    )

    result = consolidator.merge_group([memory])

    assert result["value"] == "Python"
    assert result["importance"] == 0.9


def test_merge_multiple_values():
    consolidator = MemoryConsolidator()

    memories = [
        make_memory(value="Python"),
        make_memory(value="Rust"),
    ]

    result = consolidator.merge_group(memories)

    assert result["value"] == "Python; Rust"
    assert result["content"] == (
        "favorite_language: Python; Rust"
    )


def test_merge_prefers_high_importance():
    consolidator = MemoryConsolidator()

    memories = [
        make_memory(
            value="Python",
            importance=0.4,
        ),
        make_memory(
            value="Rust",
            importance=0.9,
        ),
    ]

    result = consolidator.merge_group(memories)

    assert result["importance"] == 0.9


def test_consolidate_and_merge():
    consolidator = MemoryConsolidator()

    memories = [
        make_memory(value="Python"),
        make_memory(value="Rust"),
        make_memory(
            key="favorite_color",
            value="Blue",
        ),
    ]

    result = consolidator.consolidate_and_merge(
        memories
    )

    assert len(result) == 2
    assert any(
        memory["value"] == "Python; Rust"
        for memory in result
    )
