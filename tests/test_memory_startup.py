"""Startup and offline regressions for the optional memory embedding model."""

import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from app.memory import platform_embedding


def apple_embedding(monkeypatch):
    monkeypatch.setattr(platform_embedding.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(platform_embedding.platform, "machine", lambda: "arm64")
    return platform_embedding.create_embedding_model()


def test_startup_and_empty_input_do_not_load_embedding(monkeypatch):
    def forbidden_load():
        raise AssertionError("startup must not load or download an embedding model")

    monkeypatch.setattr(platform_embedding, "_load_cached_mlx_model", forbidden_load)
    model = apple_embedding(monkeypatch)
    assert model._model is None
    assert model.embed("") == []
    assert model.embed(None) == []
    assert model.embed_many([None, " "]) == []
    assert model._model is None


def test_missing_cache_falls_back_once_and_keeps_vectors_consistent(monkeypatch):
    attempts = []

    def missing_model():
        attempts.append(True)
        raise FileNotFoundError("no cached model")

    monkeypatch.setattr(platform_embedding, "_load_cached_mlx_model", missing_model)
    model = apple_embedding(monkeypatch)
    vector = model.embed("I like Python")
    assert len(vector) == 384
    assert model.embed_many(["I like Python", "I like Python"]) == [vector, vector]
    assert attempts == [True]


def test_parallel_first_use_loads_only_one_model(monkeypatch):
    attempts = []
    barrier = threading.Barrier(4)

    def cached_model():
        attempts.append(True)
        return platform_embedding.HashEmbeddingModel()

    monkeypatch.setattr(platform_embedding, "_load_cached_mlx_model", cached_model)
    model = apple_embedding(monkeypatch)

    def embed(_):
        barrier.wait(timeout=5)
        return model.embed("same query")

    with ThreadPoolExecutor(max_workers=4) as pool:
        vectors = list(pool.map(embed, range(4)))
    assert vectors == [vectors[0]] * 4
    assert attempts == [True]


def test_cached_model_resolution_never_uses_network(monkeypatch, tmp_path):
    calls = []
    cached = str(tmp_path / "snapshot")

    def snapshot_download(repo_id, **kwargs):
        calls.append((repo_id, kwargs))
        return cached

    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(snapshot_download=snapshot_download))
    monkeypatch.setitem(sys.modules, "app.memory.embedding_mlx", SimpleNamespace(MLXEmbeddingModel=lambda **kwargs: kwargs))
    assert platform_embedding._load_cached_mlx_model() == {"model_name": cached}
    assert calls == [("mlx-community/multilingual-e5-small-mlx", {
        "local_files_only": True,
        "allow_patterns": ["*.json", "*.safetensors", "*.py", "*.tiktoken", "*.txt", "*.model"],
    })]
