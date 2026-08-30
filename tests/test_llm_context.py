from app.llm import LLMConfig, ModelManager, LLMEngine


def test_count_tokens():
    config = LLMConfig()
    manager = ModelManager(config)
    engine = LLMEngine(manager, config)

    text = "Hello world"

    count = engine.count_tokens(text)

    assert isinstance(count, int)
    assert count > 0


def test_prompt_trimming():
    config = LLMConfig(
        max_prompt_tokens=10,
    )

    manager = ModelManager(config)
    engine = LLMEngine(manager, config)

    prompt = "Hello world " * 100

    trimmed = engine._trim_prompt(prompt)

    token_count = engine.count_tokens(trimmed)

    assert token_count <= 10


def test_prompt_not_trimmed_when_small():
    config = LLMConfig(
        max_prompt_tokens=100,
    )

    manager = ModelManager(config)
    engine = LLMEngine(manager, config)

    prompt = "Hello world"

    result = engine._trim_prompt(prompt)

    assert result == prompt
