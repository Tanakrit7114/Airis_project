import sys
import types

from app.llm_backends.mlx_backend import MLXBackend


class _Tok:
    def encode(self, text):
        return [1, 2]

    def decode(self, tokens):
        return "decoded"


def test_mlx_backend_uses_sampler(monkeypatch):
    calls = {}

    class Resp:
        text = "hello"
        generation_tokens = 1
        finish_reason = "stop"

    def fake_load(model):
        return object(), _Tok()

    def fake_stream_generate(model, tok, prompt, **kwargs):
        calls.update(kwargs)
        yield Resp()

    fake_mod = types.SimpleNamespace(load=fake_load, stream_generate=fake_stream_generate)
    monkeypatch.setitem(sys.modules, "mlx_lm", fake_mod)
    sampler = object()
    sampling = {}
    def make_sampler(**kwargs):
        sampling.update(kwargs)
        return sampler
    monkeypatch.setitem(sys.modules, "mlx_lm.sample_utils", types.SimpleNamespace(make_sampler=make_sampler))

    backend = MLXBackend("dummy-model")
    events = list(backend.stream_generate("hello", 32, 0.5, 0.9))

    assert events[0].text == "hello"
    assert calls["max_tokens"] == 32
    assert calls["sampler"] is sampler
    assert sampling == {"temp": 0.5, "top_p": 0.9}
    assert "temperature" not in calls
    assert "top_p" not in calls
