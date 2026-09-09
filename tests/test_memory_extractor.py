from app.memory.extractor import MemoryExtractor


def test_extract_preference():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "I prefer Python."
    )

    assert len(result) == 1

    memory = result[0]

    assert memory["memory_type"] == "preference"
    assert memory["subject"] == "user"
    assert memory["key"] == "favorite_language"
    assert memory["value"] == "Python"


def test_extract_like_preference():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "I like Italian food."
    )

    assert len(result) == 1
    assert result[0]["memory_type"] == "preference"
    assert result[0]["value"] == "Italian food"


def test_extract_name():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "My name is Tanakrit."
    )

    assert len(result) == 1

    assert result[0]["memory_type"] == "profile"
    assert result[0]["key"] == "name"
    assert result[0]["value"] == "Tanakrit"


def test_extract_identity():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "I am a computer engineering student."
    )

    assert len(result) == 1

    assert result[0]["memory_type"] == "profile"
    assert result[0]["key"] == "identity"


def test_extract_project():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "I am working on JARVIS."
    )

    assert len(result) == 1

    assert result[0]["memory_type"] == "project"
    assert result[0]["key"] == "current_project"
    assert result[0]["value"] == "JARVIS"


def test_extract_project_without_i_am():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "Working on a local AI assistant."
    )

    assert len(result) == 1

    assert result[0]["memory_type"] == "project"
    assert result[0]["value"] == "a local AI assistant"


def test_extract_task():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "I need to finish my ML assignment."
    )

    assert len(result) == 1

    assert result[0]["memory_type"] == "task"
    assert result[0]["key"] == "task"


def test_extract_goal():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "I want to build a local LLM."
    )

    assert len(result) == 1

    assert result[0]["memory_type"] == "task"
    assert result[0]["key"] == "goal"


def test_empty_input():
    extractor = MemoryExtractor()

    assert extractor.extract("") == []
    assert extractor.extract("   ") == []
    assert extractor.extract(None) == []


def test_extract_one():
    extractor = MemoryExtractor()

    result = extractor.extract_one(
        "I prefer Python."
    )

    assert result is not None
    assert result["value"] == "Python"


def test_extract_one_without_memory():
    extractor = MemoryExtractor()

    result = extractor.extract_one(
        "The weather is nice today."
    )

    assert result is None


def test_whitespace_normalization():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "I prefer   Python   programming."
    )

    assert len(result) == 1
    assert result[0]["value"] == "Python programming"
