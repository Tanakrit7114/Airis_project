from app.llm import LLMConfig, ModelManager, LLMEngine


def test_model_manager_unload():
    config = LLMConfig()
    manager = ModelManager(config)

    manager.model = object()
    manager.tokenizer = object()

    manager.unload()

    assert manager.model is None
    assert manager.tokenizer is None


def test_engine_shutdown():
    config = LLMConfig()
    manager = ModelManager(config)

    engine = LLMEngine(manager, config)

    manager.model = object()
    manager.tokenizer = object()

    engine.shutdown()

    assert engine._shutdown_requested is True
    assert manager.model is None
    assert manager.tokenizer is None
