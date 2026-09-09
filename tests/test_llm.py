from app.llm import LLMConfig, ModelManager, LLMEngine


def test_llm_config():
    config = LLMConfig()

    assert config.temperature == 0.3
    assert config.top_p == 0.9
    assert config.max_tokens == 512
    assert config.context_window == 8192
    assert config.max_prompt_tokens == 6144
    from app.config import LLM_RESPONSE_TIMEOUT
    assert config.timeout == LLM_RESPONSE_TIMEOUT
    assert config.max_retries == 2


def test_model_manager_initial_state():
    config = LLMConfig()

    manager = ModelManager(config)

    assert manager.model is None
    assert manager.tokenizer is None


def test_llm_engine():
    config = LLMConfig()

    manager = ModelManager(config)

    engine = LLMEngine(
        manager,
        config,
    )

    assert engine.config is config
    assert engine.model_manager is manager

def test_prompt_within_context_window():
    config = LLMConfig(
        context_window=100,
        max_prompt_tokens=80,
    )

    manager = ModelManager(config)
    engine = LLMEngine(manager, config)

    prompt = "hello " * 10

    result = engine._trim_prompt(prompt)

    assert result == prompt


def test_prompt_exceeds_context_window():
    config = LLMConfig(
        context_window=100,
        max_prompt_tokens=10,
    )
    manager = ModelManager(config)
    engine = LLMEngine(manager, config)

    prompt = "a" * 1000
    result = engine._trim_prompt(prompt)

    assert engine.count_tokens(result) <= config.max_prompt_tokens
