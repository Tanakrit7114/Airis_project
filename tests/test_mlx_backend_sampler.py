from app.llm_backends.mlx_backend import MLXBackend

def test_mlx_backend_uses_sampler(monkeypatch):
    calls = {}

    class FakeResponse:
        text = "ok"
        generation_tokens = 1
        finish_reason = "stop"

    class FakeMLXLM:
        @staticmethod
        def stream_generate(model, tok, prompt, **kwargs):
            calls.update(kwargs)
            yield FakeResponse()

    class FakeSampleUtils:
        @staticmethod
        def make_sampler(**kwargs):
            calls["sampler_args"] = kwargs
            return "SAMPLER"

    import sys, types
    fake = types.ModuleType("mlx_lm")
    fake.stream_generate = FakeMLXLM.stream_generate
    fake_sample = types.ModuleType("mlx_lm.sample_utils")
    fake_sample.make_sampler = FakeSampleUtils.make_sampler
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    monkeypatch.setitem(sys.modules, "mlx_lm.sample_utils", fake_sample)

    backend = MLXBackend("dummy")
    backend._model = object()
    backend._tokenizer = object()
    events = list(backend.stream_generate("hi", 8, 0.5, 0.9))

    assert calls["sampler_args"] == {"temp": 0.5, "top_p": 0.9}
    assert calls["sampler"] == "SAMPLER"
    assert events[0].text == "ok"
