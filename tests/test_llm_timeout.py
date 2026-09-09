
import importlib.util
import pytest

_HAS_BACKEND = importlib.util.find_spec("llama_cpp") is not None or importlib.util.find_spec("mlx_lm") is not None
pytestmark = pytest.mark.skipif(not _HAS_BACKEND, reason="LLM runtime backend not installed in test environment")
import time

import pytest

from app.llm import LLMConfig, ModelManager, LLMEngine


class FakeTokenizer:
    def apply_chat_template(
        self,
        messages,
        tokenize=False,
        add_generation_prompt=True,
    ):
        return "Hello"

    def encode(self, text):
        return text.split()

    def decode(self, tokens):
        return " ".join(tokens)


def test_timeout_config():
    config = LLMConfig(timeout=1.0)

    assert config.timeout == 1.0


def test_generation_timeout(monkeypatch):
    config = LLMConfig(
        timeout=0.01,
        max_retries=0,
    )

    manager = ModelManager(config)
    engine = LLMEngine(manager, config)

    def fake_generate(*args, **kwargs):
        time.sleep(0.05)
        return []

    monkeypatch.setattr(
        engine,
        "_generate_stream",
        fake_generate,
    )

    monkeypatch.setattr(
        manager,
        "load",
        lambda: (object(), FakeTokenizer()),
    )

    with pytest.raises(TimeoutError):
        engine.stream(
            [
                {
                    "role": "user",
                    "content": "Hello",
                }
            ]
        )