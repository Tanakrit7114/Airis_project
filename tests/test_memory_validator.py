import pytest

from app.memory.validator import MemoryValidator


def test_valid_memory():

    validator = MemoryValidator()

    memory = {
        "memory_type": "preference",
        "subject": "user",
        "key": "favorite_language",
        "value": "Python",
        "importance": 0.9,
        "confidence": 0.95,
    }

    valid, result = validator.validate(memory)

    assert valid is True
    assert result["memory_type"] == "preference"
    assert result["value"] == "Python"


def test_missing_required_field():

    validator = MemoryValidator()

    memory = {
        "memory_type": "preference",
        "subject": "user",
        "value": "Python",
    }

    with pytest.raises(ValueError):
        validator.validate(memory)


def test_invalid_memory_type():

    validator = MemoryValidator()

    memory = {
        "memory_type": "unknown",
        "subject": "user",
        "key": "test",
        "value": "value",
    }

    with pytest.raises(ValueError):
        validator.validate(memory)


def test_invalid_importance():

    validator = MemoryValidator()

    memory = {
        "memory_type": "preference",
        "subject": "user",
        "key": "test",
        "value": "value",
        "importance": 2.0,
    }

    with pytest.raises(ValueError):
        validator.validate(memory)


def test_invalid_confidence():

    validator = MemoryValidator()

    memory = {
        "memory_type": "preference",
        "subject": "user",
        "key": "test",
        "value": "value",
        "confidence": -1.0,
    }

    with pytest.raises(ValueError):
        validator.validate(memory)


def test_default_values():

    validator = MemoryValidator()

    memory = {
        "memory_type": "preference",
        "subject": "user",
        "key": "favorite_language",
        "value": "Python",
    }

    valid, result = validator.validate(memory)

    assert valid is True
    assert result["importance"] == 0.5
    assert result["confidence"] == 0.8
    assert result["tags"] == []
    assert result["entities"] == []
    assert result["relationships"] == []
    assert result["decay_rate"] == 0.0
    assert result["expires_at"] is None
