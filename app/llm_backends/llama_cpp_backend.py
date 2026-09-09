from __future__ import annotations
import os
from typing import Iterator
from .base import LLMBackend, GenerationEvent

class LlamaCppBackend(LLMBackend):
    name = "llama.cpp"
    platform = "cpu-cuda-metal-compatible"
    def __init__(self, model_path: str, n_ctx: int = 8192):
        self.model = model_path
        self.n_ctx = n_ctx
        self._llama = None

    def available(self) -> bool:
        try:
            import llama_cpp  # noqa: F401
            return True
        except ImportError:
            return False

    def load(self):
        if self._llama is None:
            try:
                from llama_cpp import Llama
            except ImportError as exc:
                raise RuntimeError("llama-cpp-python is not installed. Install it on Windows/Linux/Intel Mac.") from exc
            if not os.path.isfile(self.model):
                raise RuntimeError(f"GGUF model not found: {self.model}. Set MODEL/LLAMA_MODEL_PATH to a local .gguf file.")
            self._llama = Llama(model_path=self.model, n_ctx=self.n_ctx, n_gpu_layers=-1, verbose=False)
        return self._llama, None

    def unload(self):
        self._llama = None

    def encode(self, text: str) -> list[int]:
        llama, _ = self.load()
        return list(llama.tokenize(text.encode("utf-8"), add_bos=False))

    def decode(self, tokens: list[int]) -> str:
        llama, _ = self.load()
        return llama.detokenize(tokens).decode("utf-8", errors="ignore")

    def stream_generate(self, prompt: str, max_tokens: int, temperature: float, top_p: float) -> Iterator[GenerationEvent]:
        llama, _ = self.load()
        stream = llama.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=True,
        )
        count = 0
        for item in stream:
            choice = item.get("choices", [{}])[0]
            delta = choice.get("delta", {})
            text = delta.get("content", "") or ""
            count += 1 if text else 0
            finish = choice.get("finish_reason")
            yield GenerationEvent(text=text, generation_tokens=count, finish_reason=finish)
