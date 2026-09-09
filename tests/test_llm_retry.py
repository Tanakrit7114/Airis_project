
import importlib.util
import pytest

_HAS_BACKEND = importlib.util.find_spec("llama_cpp") is not None or importlib.util.find_spec("mlx_lm") is not None
pytestmark = pytest.mark.skipif(not _HAS_BACKEND, reason="LLM runtime backend not installed in test environment")
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
    monkeypatch.setattr(manager, "load", lambda: (None, None))

    result = engine.stream(
        [{"role": "user", "content": "Hello"}]
    )

    assert result == "Hello"
    assert calls["count"] == 3


def test_no_retry_after_visible_token(monkeypatch):
    from app.llm_backends.base import GenerationEvent
    config=LLMConfig(max_retries=2,backend="ollama")
    manager=ModelManager(config)
    engine=LLMEngine(manager,config)
    monkeypatch.setattr(manager,"load",lambda:(None,None))
    calls=[]
    def generate(*args):
        calls.append(1)
        yield GenerationEvent(text="partial")
        raise RuntimeError("temporary failure")
    monkeypatch.setattr(engine,"_generate_stream",generate)
    received=[]
    with pytest.raises(RuntimeError):
        engine.stream([{"role":"user","content":"hello"}],on_token=received.append,emit_console=False)
    assert received==["partial"]
    assert len(calls)==1


def test_timeout_never_retries(monkeypatch):
    config=LLMConfig(max_retries=2,backend="ollama")
    manager=ModelManager(config)
    engine=LLMEngine(manager,config)
    monkeypatch.setattr(manager,"load",lambda:(None,None))
    calls=[]
    def generate(*args):
        calls.append(1)
        raise TimeoutError("deadline")
    monkeypatch.setattr(engine,"_generate_stream",generate)
    with pytest.raises(TimeoutError):
        engine.stream([{"role":"user","content":"hello"}])
    assert len(calls)==1
