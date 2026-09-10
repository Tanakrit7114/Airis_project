from __future__ import annotations
import hashlib, math, platform, re, threading
from app.memory.embedding import EmbeddingModel

class HashEmbeddingModel(EmbeddingModel):
    """Dependency-light fallback used when MLX is unavailable.
    It keeps the memory pipeline functional on Windows/Linux/Intel Mac."""
    def __init__(self, dimensions: int = 384): self.dimensions=dimensions
    def embed(self,text:str):
        if not isinstance(text,str) or not text.strip(): return []
        vec=[0.0]*self.dimensions
        tokens=re.findall(r"[\wก-๙]+",text.lower())
        for token in tokens:
            digest=hashlib.blake2b(token.encode('utf-8'),digest_size=8).digest()
            idx=int.from_bytes(digest,'little')%self.dimensions
            sign=1.0 if digest[0]&1 else -1.0
            vec[idx]+=sign
        norm=math.sqrt(sum(x*x for x in vec)) or 1.0
        return [x/norm for x in vec]

def _load_cached_mlx_model():
    # Memory must not require a model download or a Hub availability check.
    # Passing a local snapshot also prevents mlx_embeddings.load from querying
    # the Hub again when the embedding model is already installed.
    from huggingface_hub import snapshot_download
    model_path = snapshot_download(
        "mlx-community/multilingual-e5-small-mlx", local_files_only=True,
        # Match mlx_embeddings' download set; documentation may be uncached.
        allow_patterns=["*.json", "*.safetensors", "*.py", "*.tiktoken", "*.txt", "*.model"],
    )
    from app.memory.embedding_mlx import MLXEmbeddingModel
    return MLXEmbeddingModel(model_name=model_path)


class _LazyMLXEmbeddingModel(EmbeddingModel):
    """Choose one embedding backend on first use, without delaying startup."""

    def __init__(self):
        self._model = None
        self._lock = threading.Lock()

    def _get_model(self):
        with self._lock:
            if self._model is None:
                try:
                    self._model = _load_cached_mlx_model()
                except Exception:
                    # Keep one backend for this index's lifetime so stored
                    # vectors and later queries stay in the same vector space.
                    self._model = HashEmbeddingModel()
            return self._model

    def embed(self, text):
        if not isinstance(text, str) or not text.strip():
            return []
        return self._get_model().embed(text)

    def embed_many(self, texts):
        if not texts:
            return []
        valid_texts = [text.strip() for text in texts if isinstance(text, str) and text.strip()]
        if not valid_texts:
            return []
        return self._get_model().embed_many(valid_texts)


def create_embedding_model():
    if platform.system()=="Darwin" and platform.machine().lower() in {"arm64","aarch64"}:
        return _LazyMLXEmbeddingModel()
    return HashEmbeddingModel()
