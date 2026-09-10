import asyncio
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.server.routes import models


@pytest.fixture
def model_client(monkeypatch):
    calls = []

    def engine():
        config = SimpleNamespace(model="original")
        manager = SimpleNamespace(status="ready", backend_name="mlx")

        def switch(model, backend, load=True):
            calls.append((model, backend, load))
            config.model = model
            manager.backend_name = backend

        manager.switch_model = switch
        return SimpleNamespace(config=config, model_manager=manager)

    state = SimpleNamespace(
        lock=asyncio.Lock(), chat_provider="local", kku_model=None,
        assistant=SimpleNamespace(llm=engine(), rag_llm=engine()),
    )
    monkeypatch.setattr(models, "state", lambda: state)
    monkeypatch.setattr(models, "catalog", lambda: [
        {"id": "llama3.2:latest", "backend": "ollama"},
        {"id": "cloud-model", "backend": "kku"},
        {"id": "shared-name", "backend": "ollama"},
        {"id": "shared-name", "backend": "kku"},
    ])
    monkeypatch.setenv("KKU_API_KEY", "fake-test-key")
    app = FastAPI()
    app.include_router(models.router)
    with TestClient(app) as client:
        yield client, state, calls


def test_selection_infers_catalog_backend_instead_of_previous_backend(model_client):
    client, state, calls = model_client
    response = client.post("/api/models/select", json={"model": "llama3.2:latest"})
    assert response.status_code == 200
    assert calls == [("llama3.2:latest", "ollama", True)]
    assert response.json()["backend"] == "ollama"
    assert state.chat_provider == "local"


@pytest.mark.parametrize("endpoint", ["select", "rag/select"])
def test_selection_rejects_wrong_backend_without_mutating_model(model_client, endpoint):
    client, state, calls = model_client
    response = client.post(f"/api/models/{endpoint}", json={"model": "llama3.2:latest", "backend": "mlx"})
    assert response.status_code == 400
    assert calls == []
    assert state.assistant.llm.config.model == "original"


def test_cloud_selection_without_backend_uses_cloud_provider(model_client):
    client, state, calls = model_client
    response = client.post("/api/models/select", json={"model": "cloud-model"})
    assert response.status_code == 200
    assert state.chat_provider == "kku"
    assert state.kku_model == "cloud-model"
    assert calls == []


def test_cloud_selection_requires_key(model_client, monkeypatch):
    client, state, calls = model_client
    monkeypatch.delenv("KKU_API_KEY")
    response = client.post("/api/models/select", json={"model": "cloud-model", "backend": "kku"})
    assert response.status_code == 400
    assert state.chat_provider == "local"
    assert calls == []


def test_rag_rejects_cloud_without_changing_local_model(model_client):
    client, state, calls = model_client
    response = client.post("/api/models/rag/select", json={"model": "cloud-model", "backend": "kku"})
    assert response.status_code == 400
    assert calls == []
    assert state.assistant.rag_llm.config.model == "original"


def test_same_model_name_requires_backend_and_accepts_explicit_choice(model_client):
    client, state, calls = model_client
    assert client.post("/api/models/select", json={"model": "shared-name"}).status_code == 400
    response = client.post("/api/models/select", json={"model": "shared-name", "backend": "ollama"})
    assert response.status_code == 200
    assert calls == [("shared-name", "ollama", True)]


def test_catalog_includes_all_installed_ollama_models(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(models.platform, "system", lambda: "Linux")
    monkeypatch.setattr(models, "state", lambda: SimpleNamespace(
        assistant=SimpleNamespace(llm=SimpleNamespace(config=SimpleNamespace(model="missing.gguf")))))
    monkeypatch.setattr(models, "kku_catalog", lambda: [])
    response = SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"models": [
        {"name": "llama3.2:latest", "size": 2 * 1024**3},
        {"name": "qwen3:14b"}, None, {"name": 123},
    ]})
    monkeypatch.setattr(models.requests, "get", lambda *args, **kwargs: response)
    catalog = models.catalog()
    installed = [item for item in catalog if item["backend"] == "ollama" and item["installed"]]
    assert {item["id"] for item in installed} == {"llama3.2:latest", "qwen3:14b"}
    assert next(item for item in installed if item["id"] == "llama3.2:latest")["size"] == "2.0 GB"
