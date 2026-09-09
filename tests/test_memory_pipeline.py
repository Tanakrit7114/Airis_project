# Phase 1.1 — Memory 2.0

from app.memory.pipeline import MemoryPipeline


def test_pipeline_extract_preference():

    pipeline = MemoryPipeline()

    result = pipeline.process(
        "I prefer Python."
    )

    assert len(result) == 1

    memory = result[0]

    assert memory["memory_type"] == "preference"
    assert memory["subject"] == "user"
    assert memory["key"] == "favorite_language"
    assert memory["value"] == "Python"


def test_pipeline_empty_input():

    pipeline = MemoryPipeline()

    assert pipeline.process("") == []


def test_pipeline_invalid_input():

    pipeline = MemoryPipeline()

    assert pipeline.process(None) == []


def test_pipeline_project():

    pipeline = MemoryPipeline()

    result = pipeline.process(
        "I am working on JARVIS."
    )

    assert len(result) == 1

    memory = result[0]

    assert memory["memory_type"] == "project"
    assert memory["key"] == "current_project"
    assert memory["value"] == "JARVIS"


def test_pipeline_scores_memory():

    pipeline = MemoryPipeline()

    result = pipeline.process(
        "I prefer Python."
    )

    memory = result[0]

    assert "importance" in memory
    assert "confidence" in memory

    assert 0.0 <= memory["importance"] <= 1.0
    assert 0.0 <= memory["confidence"] <= 1.0


def test_pipeline_contradiction():

    pipeline = MemoryPipeline()

    existing = [
        {
            "memory_type": "preference",
            "subject": "user",
            "key": "favorite_language",
            "value": "Python",
        }
    ]

    result = pipeline.process(
        "I prefer Rust.",
        existing,
    )

    assert len(result) == 1

    memory = result[0]

    assert memory["key"] == "favorite_language"
    assert memory["value"] == "Rust"

    assert "contradictions" in memory

    assert len(memory["contradictions"]) >= 1
