from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.server import kku_fallback as kku
from app.server.routes import models


@pytest.fixture(autouse=True)
def isolated_telemetry(monkeypatch):
    monkeypatch.setenv("KKU_API_KEY", "telemetry-account-a")
    monkeypatch.setenv("KKU_CHAT_MODELS", "configured-model")
    monkeypatch.setattr(kku, "_OBSERVED_USAGE", {})
    monkeypatch.setattr(kku, "_OBSERVED_ACCOUNT", None)
    monkeypatch.setattr(models, "_KKU_CACHE", {"signature": "", "expires": 0.0, "models": []})
    monkeypatch.setattr(kku.requests, "post", lambda *a, **kw: pytest.fail("unexpected completion call"))
    monkeypatch.setattr(models.requests, "get", lambda *a, **kw: pytest.fail("unexpected catalogue call"))


def test_actual_completion_records_zero_quota_and_numeric_strings(monkeypatch):
    response = SimpleNamespace(status_code=200, json=lambda: {
        "choices": [{"message": {"content": "answer"}}],
        "usage": {"prompt_tokens": "12", "completion_tokens": 3, "total_tokens": "15.0"},
        "model_quota": {"daily_quota_tokens": "15", "daily_remaining_tokens": "0"},
    })
    monkeypatch.setattr(kku.requests, "post", lambda *a, **kw: response)
    assert kku._call("telemetry-account-a", "model-a", [], 4096) == "answer"
    record = kku.observed_model_usage()["model-a"]
    assert record["usage"] == {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15}
    assert record["model_quota"]["daily_remaining_tokens"] == 0
    assert record["quota_seen_at"] == record["last_seen"]


def test_invalid_numeric_values_cannot_break_json_or_become_quota():
    kku._record_usage("model-a", {"model_quota": {
        "daily_remaining_tokens": 0,
        "nan_number": float("nan"), "nan_string": "NaN", "infinity": float("inf"),
        "overflow": "1e9999", "negative": -1, "negative_string": "-5", "bool": True,
        "object": {}, "none": None, "text": "not provided",
    }})
    assert kku.observed_model_usage()["model-a"]["model_quota"] == {"daily_remaining_tokens": 0}


def test_key_change_and_late_old_response_do_not_expose_previous_account(monkeypatch):
    kku._record_usage("model-a", {"model_quota": {"daily_remaining_tokens": 100}})
    monkeypatch.setenv("KKU_API_KEY", "telemetry-account-b")
    assert kku.observed_model_usage() == {}
    kku._record_usage("model-a", {"model_quota": {"daily_remaining_tokens": 20}})
    kku._record_usage("model-a", {"model_quota": {"daily_remaining_tokens": 90}}, api_key="telemetry-account-a")
    assert kku.observed_model_usage()["model-a"]["model_quota"]["daily_remaining_tokens"] == 20
    monkeypatch.delenv("KKU_API_KEY")
    assert kku.observed_model_usage() == {}
    kku._record_usage("model-a", {"model_quota": {"daily_remaining_tokens": 10}}, api_key="telemetry-account-b")
    assert kku.observed_model_usage() == {}


def test_usage_only_response_preserves_quota_timestamp_and_returns_independent_copy(monkeypatch):
    monkeypatch.setattr(kku.time, "time", lambda: 100.0)
    kku._record_usage("model-a", {"model_quota": {"daily_remaining_tokens": 50}})
    monkeypatch.setattr(kku.time, "time", lambda: 200.0)
    kku._record_usage("model-a", {"usage": {"total_tokens": 2}})
    observed = kku.observed_model_usage()
    assert observed["model-a"]["quota_seen_at"] == 100.0
    assert observed["model-a"]["usage_seen_at"] == 200.0
    observed["model-a"]["model_quota"]["daily_remaining_tokens"] = 999
    assert kku.observed_model_usage()["model-a"]["model_quota"]["daily_remaining_tokens"] == 50


def test_cached_catalog_refreshes_usage_without_probing_completion_or_mutating_cache(monkeypatch):
    calls = []

    def catalogue(*args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"data": [{
            "id": "model-a", "context_window": "32000", "max_output_tokens": 8000,
        }]})

    monkeypatch.setattr(models.requests, "get", catalogue)
    first = models.kku_catalog()
    assert first[0]["observed"] is None
    first[0]["limits"]["context_window"] = -1
    kku._record_usage("model-a", {"model_quota": {"daily_remaining_tokens": 0}})
    second = models.kku_catalog()
    assert len(calls) == 1
    assert second[0]["limits"]["context_window"] == 32000
    assert second[0]["limits"]["usage_available"] is True
    assert second[0]["observed"]["model_quota"]["daily_remaining_tokens"] == 0
    assert models._KKU_CACHE["models"][0]["observed"] is None


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "1e999", "NaN", True, -1, 0, 1.5])
def test_invalid_context_limits_are_unknown(value):
    assert models._kku_limits({"context_window": value})["context_window"] is None


def test_generic_max_tokens_is_not_mislabelled_as_context_and_vision_matches_text_route():
    assert models._kku_limits({"max_tokens": 4096})["context_window"] is None
    for model in ("gemini-3.8-flash", "gpt-4o", "qwen2-vl", "text-model"):
        caps = models._kku_capabilities(model)
        assert caps["vision"] is False
        assert caps["image_generation"] is False
        assert caps["website_generation"] is True


def test_models_endpoint_reports_exhausted_quota_without_credentials(monkeypatch):
    engine = SimpleNamespace(config=SimpleNamespace(model="local"),
                             model_manager=SimpleNamespace(backend_name="mlx", status="ready"))
    monkeypatch.setattr(models, "state", lambda: SimpleNamespace(
        chat_provider="kku", kku_model="model-a", assistant=SimpleNamespace(llm=engine, rag_llm=engine)))
    monkeypatch.setattr(models, "catalog", lambda: [models._kku_item("model-a")])
    kku._record_usage("model-a", {"model_quota": {"daily_remaining_tokens": 0}})
    app = FastAPI()
    app.include_router(models.router)
    with TestClient(app) as client:
        response = client.get("/api/models")
    assert response.status_code == 200
    payload = response.json()
    assert payload["kku"]["usage_available"] is True
    assert payload["models"][0]["limits"]["usage_available"] is True
    assert payload["models"][0]["observed"]["model_quota"]["daily_remaining_tokens"] == 0
    assert "telemetry-account-a" not in response.text
    assert kku._account_signature("telemetry-account-a") not in response.text


def test_malformed_catalogue_uses_configured_fallback(monkeypatch):
    monkeypatch.setattr(models.requests, "get", lambda *a, **kw: SimpleNamespace(
        raise_for_status=lambda: None, json=lambda: ["unexpected payload"]))
    assert models.kku_catalog()[0]["id"] == "configured-model"
