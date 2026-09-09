from __future__ import annotations
from typing import Iterator, Any
from .base import LLMBackend, GenerationEvent

class MLXBackend(LLMBackend):
    name = "mlx"
    platform = "macos-apple-silicon"
    def __init__(self, model: str):
        self.model = model
        self._model = None
        self._tokenizer = None

    def available(self) -> bool:
        try:
            import mlx  # noqa: F401
            import mlx_lm  # noqa: F401
            return True
        except ImportError:
            return False

    def load(self):
        if self._model is None:
            try:
                from mlx_lm import load
            except ImportError as exc:
                raise RuntimeError("MLX-LM is unavailable. Use macOS Apple Silicon or select a llama.cpp model.") from exc
            self._model, self._tokenizer = load(self.model)
        return self._model, self._tokenizer

    def unload(self):
        self._model = None
        self._tokenizer = None
        try:
            import mlx.core as mx
            mx.clear_cache()
        except Exception:
            pass

    def encode(self, text: str) -> list[int]:
        _, tok = self.load()
        return tok.encode(text)

    def decode(self, tokens: list[int]) -> str:
        _, tok = self.load()
        return tok.decode(tokens)

    def stream_generate(self, prompt: str, max_tokens: int, temperature: float, top_p: float) -> Iterator[GenerationEvent]:
        from mlx_lm import stream_generate
        model, tok = self.load()
        # mlx-lm 0.31.x passes sampling through ``sampler`` rather than
        # ``temperature``/``top_p`` directly to generate_step.
        # See mlx_lm.sample_utils.make_sampler for the supported API.
        try:
            from mlx_lm.sample_utils import make_sampler
            sampler = make_sampler(temp=temperature, top_p=top_p)
            responses = stream_generate(
                model, tok, prompt, max_tokens=max_tokens, sampler=sampler
            )
        except (TypeError, ImportError):
            # Conservative fallback for older/incompatible mlx-lm versions.
            responses = stream_generate(model, tok, prompt, max_tokens=max_tokens)
        for response in responses:
            yield GenerationEvent(
                text=getattr(response, "text", "") or "",
                generation_tokens=getattr(response, "generation_tokens", None),
                finish_reason=getattr(response, "finish_reason", None) or getattr(response, "stop_reason", None),
            )
