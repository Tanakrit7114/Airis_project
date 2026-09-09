from app.memory.confidence import ConfidenceScorer


def make_memory(**overrides):
    memory = {
        "memory_type": "preference",
        "subject": "user",
        "key": "favorite_language",
        "value": "Python",
        "source": "conversation",
    }

    memory.update(overrides)

    return memory


def test_default_confidence():
    scorer = ConfidenceScorer()

    score = scorer.score()

    assert 0.0 <= score <= 1.0
    assert score == 0.8


def test_explicit_confidence():
    scorer = ConfidenceScorer()

    memory = make_memory(
        confidence=0.95
    )

    assert scorer.score(memory) == 0.95


def test_confidence_is_clamped():
    scorer = ConfidenceScorer()

    assert scorer.score(
        make_memory(confidence=2.0)
    ) == 1.0

    assert scorer.score(
        make_memory(confidence=-1.0)
    ) == 0.0


def test_uncertain_statement_reduces_confidence():
    scorer = ConfidenceScorer()

    memory = make_memory(
        value="Maybe Rust",
    )

    score = scorer.score(memory)

    assert score < 0.8


def test_strong_statement_increases_confidence():
    scorer = ConfidenceScorer()

    memory = make_memory(
        value="My favorite language is Python",
    )

    score = scorer.score(memory)

    assert score > 0.8


def test_inference_reduces_confidence():
    scorer = ConfidenceScorer()

    memory = make_memory(
        source="inference",
    )

    score = scorer.score(memory)

    assert score < 0.8


def test_user_statement_has_high_confidence():
    scorer = ConfidenceScorer()

    memory = make_memory(
        source="user",
        value="My favorite language is Python",
    )

    score = scorer.score(memory)

    assert score > 0.8


def test_calculate_alias():
    scorer = ConfidenceScorer()

    memory = make_memory(
        confidence=0.9
    )

    assert scorer.calculate(memory) == 0.9


def test_update_confidence():
    scorer = ConfidenceScorer()

    memory = make_memory()

    updated = scorer.update(
        memory,
        confidence=0.95,
    )

    assert updated["confidence"] == 0.95
    assert memory.get("confidence") is None
