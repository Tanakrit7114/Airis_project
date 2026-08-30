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
