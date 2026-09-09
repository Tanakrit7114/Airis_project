# Phase 3.2 — MLX Local Embedding

import numpy as np
import mlx.core as mx

from mlx_embeddings.utils import load

from app.memory.embedding import EmbeddingModel


class MLXEmbeddingModel(EmbeddingModel):
    """
    Local embedding model using MLX Embeddings.
    """

    def __init__(
        self,
        model_name="mlx-community/multilingual-e5-small-mlx",
    ):
        self.model_name = model_name
        self.model, self.tokenizer = load(model_name)

    def _encode(self, texts):
        """
        Encode texts using the raw MLX model.
        """

        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="mlx",
        )

        outputs = self.model(
            encoded["input_ids"],
            encoded.get("attention_mask"),
        )

        if hasattr(outputs, "text_embeds"):
            embeddings = outputs.text_embeds
        else:
            embeddings = outputs

        return np.asarray(embeddings)

    def embed(self, text: str):
        """
        Convert text into a normalized embedding vector.
        """

        if not isinstance(text, str):
            return []

        text = text.strip()

        if not text:
            return []

        embeddings = self._encode([text])

        vector = np.asarray(embeddings[0], dtype=np.float32)

        norm = np.linalg.norm(vector)

        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def embed_many(self, texts):
        """
        Convert multiple texts into normalized vectors.
        """

        if not texts:
            return []

        valid_texts = [
            text.strip()
            for text in texts
            if isinstance(text, str)
            and text.strip()
        ]

        if not valid_texts:
            return []

        vectors = np.asarray(
            self._encode(valid_texts),
            dtype=np.float32,
        )

        norms = np.linalg.norm(
            vectors,
            axis=1,
            keepdims=True,
        )

        norms[norms == 0] = 1.0

        vectors = vectors / norms

        return vectors.tolist()