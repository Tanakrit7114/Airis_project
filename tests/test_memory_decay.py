from datetime import datetime, timedelta, timezone

from app.memory.decay import MemoryDecay


def test_decay_reduces_importance():
    decay = MemoryDecay()

    result = decay.calculate(
        importance=1.0,
        age_days=10,
        decay_rate=0.1,
    )

    assert result < 1.0
    assert result > 0.0


def test_zero_age_keeps_importance():
    decay = MemoryDecay()

    result = decay.calculate(
        importance=0.8,
        age_days=0,
        decay_rate=0.1,
    )

    assert result == 0.8


def test_zero_decay_rate_keeps_importance():
    decay = MemoryDecay()

    result = decay.calculate(
        importance=0.8,
        age_days=100,
        decay_rate=0.0,
    )

    assert result == 0.8


def test_decay_never_goes_below_zero():
    decay = MemoryDecay()

    result = decay.calculate(
        importance=0.8,
        age_days=100000,
        decay_rate=1.0,
    )

    assert result >= 0.0


def test_age_days():
    decay = MemoryDecay()

    now = datetime(
        2026,
        8,
        30,
        tzinfo=timezone.utc,
    )

    accessed = now - timedelta(days=5)

    result = decay.age_days(
        accessed,
        now=now,
    )

    assert result == 5.0


def test_decay_memory():
    decay = MemoryDecay()

    now = datetime(
        2026,
        8,
        30,
        tzinfo=timezone.utc,
    )

    memory = {
        "importance": 1.0,
        "decay_rate": 0.1,
        "last_accessed": (
            now - timedelta(days=10)
        ),
    }

    result = decay.decay_memory(
        memory,
        now=now,
    )

    assert result["importance"] < 1.0
    assert result is not memory


def test_missing_last_accessed():
    decay = MemoryDecay()

    memory = {
        "importance": 0.7,
        "decay_rate": 0.1,
    }

    result = decay.decay_memory(memory)

    assert result["importance"] == 0.7


def test_not_expired_without_expiration():
    decay = MemoryDecay()

    memory = {
        "importance": 0.8,
    }

    assert not decay.is_expired(memory)


def test_expired_memory():
    decay = MemoryDecay()

    now = datetime(
        2026,
        8,
        30,
        tzinfo=timezone.utc,
    )

    memory = {
        "expires_at": (
            now - timedelta(days=1)
        ),
    }

    assert decay.is_expired(
        memory,
        now=now,
    )
