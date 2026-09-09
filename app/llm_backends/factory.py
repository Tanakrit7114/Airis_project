from __future__ import annotations
import platform
from .base import LLMBackend
from .mlx_backend import MLXBackend
from .llama_cpp_backend import LlamaCppBackend
from .ollama_backend import OllamaBackend

def select_backend(model: str, override: str = "auto") -> LLMBackend:
    if override == "ollama" or (override == "auto" and model.lower().startswith(("qwen2.5-coder:", "qwen3:", "qwen3-coder:", "qwen3.6:", "devstral-"))):
        return OllamaBackend(model)
    system = platform.system().lower()
    machine = platform.machine().lower()
    if override == "mlx" or (override == "auto" and system == "darwin" and machine in {"arm64", "aarch64"} and not model.lower().endswith(".gguf")):
        backend = MLXBackend(model)
        if backend.available() or override == "mlx":
            return backend
    return LlamaCppBackend(model)
