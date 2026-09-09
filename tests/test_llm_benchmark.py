
import importlib.util
import pytest

_HAS_BACKEND = importlib.util.find_spec("llama_cpp") is not None or importlib.util.find_spec("mlx_lm") is not None
pytestmark = pytest.mark.skipif(not _HAS_BACKEND, reason="LLM runtime backend not installed in test environment")
from app.llm import LLMConfig, ModelManager, LLMEngine


def test_benchmark():
    config = LLMConfig(
        max_tokens=8,
    )

    manager = ModelManager(config)
    engine = LLMEngine(manager, config)

    result = engine.benchmark(
        [
            {
                "role": "user",
                "content": "Say hello.",
            }
        ]
    )

    assert "tokens" in result
    assert "total_time" in result
    assert "ttft" in result
    assert "tokens_per_sec" in result

    assert result["tokens"] >= 0
    assert result["total_time"] >= 0
