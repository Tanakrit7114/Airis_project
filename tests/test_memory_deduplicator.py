from app.memory.deduplicator import MemoryDeduplicator


def make_memory(
    memory_type="preference",
    subject="user",
    key="favorite_language",
    value="Python",
):
    return {
        "memory_type": memory_type,
        "subject": subject,
        "key": key,
        "value": value,
    }


def test_exact_duplicate():

    deduplicator = MemoryDeduplicator()

    existing = [
        make_memory()
    ]

    new_memory = make_memory()

    assert deduplicator.is_duplicate(
        new_memory,
        existing,
    )


def test_different_value_is_not_duplicate():

    deduplicator = MemoryDeduplicator()

    existing = [
        make_memory(value="Python")
    ]

    new_memory = make_memory(
        value="Rust"
    )

    assert not deduplicator.is_duplicate(
        new_memory,
        existing,
    )


def test_case_difference_is_duplicate():

    deduplicator = MemoryDeduplicator()

    existing = [
        make_memory(value="Python")
    ]

    new_memory = make_memory(
        value="python"
    )

    assert deduplicator.is_duplicate(
        new_memory,
        existing,
    )


def test_whitespace_difference_is_duplicate():

    deduplicator = MemoryDeduplicator()

    existing = [
        make_memory(value="Python")
    ]

    new_memory = make_memory(
        value="  Python  "
    )

    assert deduplicator.is_duplicate(
        new_memory,
        existing,
    )


def test_different_memory_type_is_not_duplicate():

    deduplicator = MemoryDeduplicator()

    existing = [
        make_memory(
            memory_type="preference"
        )
    ]

    new_memory = make_memory(
        memory_type="project"
    )

    assert not deduplicator.is_duplicate(
        new_memory,
        existing,
    )


def test_different_subject_is_not_duplicate():

    deduplicator = MemoryDeduplicator()

    existing = [
        make_memory(
            subject="user"
        )
    ]

    new_memory = make_memory(
        subject="project"
    )

    assert not deduplicator.is_duplicate(
        new_memory,
        existing,
    )


def test_filter_duplicates():

    deduplicator = MemoryDeduplicator()

    existing = [
        make_memory(value="Python")
    ]

    memories = [
        make_memory(value="Python"),
        make_memory(value="Rust"),
    ]

    result = deduplicator.filter_duplicates(
        memories,
        existing,
    )

    assert len(result) == 1
    assert result[0]["value"] == "Rust"


def test_filter_duplicates_inside_batch():

    deduplicator = MemoryDeduplicator()

    memories = [
        make_memory(value="Python"),
        make_memory(value="Python"),
    ]

    result = deduplicator.filter_duplicates(
        memories,
        [],
    )

    assert len(result) == 1
    assert result[0]["value"] == "Python"
