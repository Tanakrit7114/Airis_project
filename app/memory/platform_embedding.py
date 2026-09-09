from __future__ import annotations
import hashlib, math, platform, re
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

def create_embedding_model():
    if platform.system()=="Darwin" and platform.machine().lower() in {"arm64","aarch64"}:
        try:
            from app.memory.embedding_mlx import MLXEmbeddingModel
            return MLXEmbeddingModel()
        except Exception:
            pass
    return HashEmbeddingModel()
