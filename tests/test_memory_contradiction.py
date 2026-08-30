from app.memory.contradiction import ContradictionDetector


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


def test_different_value_is_contradiction():

    detector = ContradictionDetector()

    existing = [
        make_memory(value="Python")
    ]

    new_memory = make_memory(
        value="Rust"
    )

    assert detector.is_contradiction(
        new_memory,
        existing,
    )


def test_same_value_is_not_contradiction():

    detector = ContradictionDetector()

    existing = [
        make_memory(value="Python")
    ]

    new_memory = make_memory(
        value="Python"
    )

    assert not detector.is_contradiction(
        new_memory,
        existing,
    )


def test_different_key_is_not_contradiction():

    detector = ContradictionDetector()

    existing = [
        make_memory(
            key="favorite_language",
            value="Python",
        )
    ]

    new_memory = make_memory(
        key="favorite_color",
        value="Blue",
    )

    assert not detector.is_contradiction(
        new_memory,
        existing,
    )


def test_different_subject_is_not_contradiction():

    detector = ContradictionDetector()

    existing = [
        make_memory(
            subject="user",
            value="Python",
        )
    ]

    new_memory = make_memory(
        subject="project",
        value="Rust",
    )

    assert not detector.is_contradiction(
        new_memory,
        existing,
    )


def test_different_memory_type_is_not_contradiction():

    detector = ContradictionDetector()

    existing = [
        make_memory(
            memory_type="preference",
            value="Python",
        )
    ]

    new_memory = make_memory(
        memory_type="project",
        value="Rust",
    )

    assert not detector.is_contradiction(
        new_memory,
        existing,
    )


def test_find_contradictions():

    detector = ContradictionDetector()

    existing = [
        make_memory(value="Python"),
        make_memory(
            key="favorite_color",
            value="Blue",
        ),
    ]

    new_memory = make_memory(
        value="Rust"
    )

    result = detector.find_contradictions(
        new_memory,
        existing,
    )

    assert len(result) == 1
    assert result[0]["value"] == "Python"


def test_normalization():

    detector = ContradictionDetector()

    existing = [
        make_memory(
            value="Python"
        )
    ]

    new_memory = make_memory(
        value="  Rust  "
    )

    assert detector.is_contradiction(
        new_memory,
        existing,
    )
