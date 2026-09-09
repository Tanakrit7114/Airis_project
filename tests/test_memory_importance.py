from app.memory.importance import ImportanceScorer


def make_memory(
    memory_type="semantic",
    content="Python is a programming language",
    importance=None,
):
    memory = {
        "memory_type": memory_type,
        "content": content,
    }

    if importance is not None:
        memory["importance"] = importance

    return memory


def test_score_returns_valid_range():
    scorer = ImportanceScorer()

    score = scorer.score(
        make_memory()
    )

    assert 0.0 <= score <= 1.0


def test_invalid_memory_returns_zero():
    scorer = ImportanceScorer()

    assert scorer.score(None) == 0.0
    assert scorer.score([]) == 0.0


def test_profile_memory_is_important():
    scorer = ImportanceScorer()

    score = scorer.score(
        make_memory(
            memory_type="profile"
        )
    )

    assert score > 0.5


def test_preference_memory_is_important():
    scorer = ImportanceScorer()

    score = scorer.score(
        make_memory(
            memory_type="preference"
        )
    )

    assert score > 0.5


def test_important_keyword_increases_score():
    scorer = ImportanceScorer()

    normal = scorer.score(
        make_memory(
            content="Python is a language"
        )
    )

    important = scorer.score(
        make_memory(
            content="Python is my favorite language"
        )
    )

    assert important > normal


def test_goal_memory_is_high_importance():
    scorer = ImportanceScorer()

    score = scorer.score(
        make_memory(
            memory_type="task",
            content="My goal is to build JARVIS"
        )
    )

    assert score > 0.5


def test_explicit_importance_is_respected():
    scorer = ImportanceScorer()

    memory = make_memory(
        importance=0.9
    )

    score = scorer.score(memory)

    assert score > 0.6


def test_score_and_update():
    scorer = ImportanceScorer()

    memory = make_memory()

    result = scorer.score_and_update(
        memory
    )

    assert result is not None
    assert "importance" in result
    assert 0.0 <= result["importance"] <= 1.0


def test_score_and_update_does_not_modify_original():
    scorer = ImportanceScorer()

    memory = make_memory()

    original = memory.copy()

    scorer.score_and_update(memory)

    assert memory == original
