from app.llm_backends.factory import select_backend
from app.llm_backends.ollama_backend import OllamaBackend
import pytest

@pytest.mark.parametrize("override", ["auto", "ollama"])
def test_ollama_does_not_fall_through_to_llama_cpp(override):
    backend=select_backend("qwen2.5-coder:7b", override)
    assert isinstance(backend, OllamaBackend)
    assert backend.model=="qwen2.5-coder:7b"
