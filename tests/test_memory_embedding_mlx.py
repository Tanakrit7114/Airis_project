import pytest
pytest.importorskip("mlx")
# Phase 3.2 — MLX Embedding Tests

import numpy as np

from app.memory.embedding_mlx import MLXEmbeddingModel


def test_mlx_embedding_model_loads():

    model = MLXEmbeddingModel()

    assert model.model is not None
    assert model.tokenizer is not None


def test_embed_returns_vector():

    model = MLXEmbeddingModel()

    vector = model.embed(
        "I like Python."
    )

    assert isinstance(vector, list)
    assert len(vector) > 0


def test_embed_vector_is_normalized():

    model = MLXEmbeddingModel()

    vector = model.embed(
        "I like Python."
    )

    norm = np.linalg.norm(
        np.asarray(vector)
    )

    assert np.isclose(
        norm,
        1.0,
        atol=1e-5,
    )


def test_empty_text():

    model = MLXEmbeddingModel()

    assert model.embed("") == []


def test_invalid_text():

    model = MLXEmbeddingModel()

    assert model.embed(None) == []


def test_embed_many():

    model = MLXEmbeddingModel()

    vectors = model.embed_many(
        [
            "I like Python.",
            "I like Italian food.",
        ]
    )

    assert isinstance(vectors, list)
    assert len(vectors) == 2
    assert len(vectors[0]) > 0
    assert len(vectors[1]) > 0


def test_similar_sentences_have_similarity():

    model = MLXEmbeddingModel()

    a = np.asarray(
        model.embed(
            "I prefer Python."
        )
    )

    b = np.asarray(
        model.embed(
            "Python is my favorite programming language."
        )
    )

    similarity = float(
        np.dot(a, b)
    )

    assert similarity > 0.5
