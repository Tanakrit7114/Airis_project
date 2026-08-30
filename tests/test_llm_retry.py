from app.llm import LLMConfig, ModelManager, LLMEngine


def test_retry_config():
    config = LLMConfig()

    assert config.max_retries == 2


def test_retry_on_generation_failure(monkeypatch):
    config = LLMConfig(
        max_retries=2,
    )

    manager = ModelManager(config)
    engine = LLMEngine(manager, config)

    class FakeResponse:
        text = "Hello"

    calls = {"count": 0}

    def fake_generate(*args, **kwargs):
        calls["count"] += 1

        if calls["count"] < 3:
            raise RuntimeError("temporary failure")

        return iter([FakeResponse()])

    monkeypatch.setattr(
        engine,
        "_generate_stream",
        fake_generate,
    )

    result = engine.stream(
        [{"role": "user", "content": "Hello"}]
    )

    assert result == "Hello"
    assert calls["count"] == 3	
