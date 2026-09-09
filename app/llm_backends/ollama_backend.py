from __future__ import annotations
import json
from typing import Iterator
import requests
from .base import LLMBackend, GenerationEvent


class OllamaBackend(LLMBackend):
    """Local Ollama backend. Models are kept and served by the Ollama daemon."""
    name = "ollama"
    platform = "local-ollama"

    def __init__(self, model: str, base_url: str = "http://127.0.0.1:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def available(self) -> bool:
        try:
            return requests.get(f"{self.base_url}/api/tags", timeout=2).ok
        except requests.RequestException:
            return False

    def load(self):
        if not self.available():
            raise RuntimeError("Ollama is not running. Start Ollama and verify the selected model is installed.")
        return self.model, None

    def unload(self):
        # Do not forcibly evict the model; Ollama owns its process and cache.
        return None

    def encode(self, text: str) -> list[int]:
        # Exact tokenisation is unnecessary for prompt trimming with this backend.
        return list(range(max(1, len(text.split()))))

    def decode(self, tokens: list[int]) -> str:
        return ""

    def stream_generate(self, prompt: str, max_tokens: int, temperature: float, top_p: float) -> Iterator[GenerationEvent]:
        payload = {"model": self.model, "prompt": prompt, "stream": True,
                   "options": {"num_predict": max_tokens, "temperature": temperature, "top_p": top_p}}
        # A short voice budget must produce an answer, not be exhausted solely
        # by hidden reasoning. Ollama's switch belongs at the top level.
        if self.model.split("/")[-1].startswith(("qwen3:", "qwen3.5:", "qwen3.6:")):
            payload["think"] = False
        try:
            with requests.post(f"{self.base_url}/api/generate", json=payload, stream=True, timeout=(10, 180)) as response:
                response.raise_for_status()
                generated = 0
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    event = json.loads(line)
                    text = event.get("response", "")
                    generated += max(1, len(text.split())) if text else 0
                    yield GenerationEvent(text=text, generation_tokens=generated,
                                          finish_reason=event.get("done_reason") if event.get("done") else None)
        except requests.RequestException as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
