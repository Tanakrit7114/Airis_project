from app.llm import LLMConfig, ModelManager, LLMEngine


def test_llm_config():
    config = LLMConfig()

    assert config.temperature == 0.7
    assert config.top_p == 0.9
    assert config.max_tokens == 512
    assert config.context_window == 8192
    assert config.max_prompt_tokens == 6144
    assert config.timeout == 120.0
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