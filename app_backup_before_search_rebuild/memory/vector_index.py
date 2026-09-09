# Phase 3.4 — Memory Vector Index

from app.memory.embedding_mlx import MLXEmbeddingModel
from app.memory.vector_store import MemoryVectorStore


class MemoryVectorIndex:
    """
    Connects the embedding model with the vector store.

    Flow:

        Memory
          ↓
        Embedding
          ↓
        VectorStore
    """

    def __init__(
        self,
        embedding_model=None,
        vector_store=None,
    ):
        self.embedding_model = (
            embedding_model
            or MLXEmbeddingModel()
        )

        self.vector_store = (
            vector_store
            or MemoryVectorStore()
        )

    # ========================================================
    # Index one memory
    # ========================================================

    def index_memory(self, memory):
        """
        Create and store an embedding for one memory.
        """

        if not isinstance(memory, dict):
            return False

        memory_id = memory.get("memory_id")

        if not memory_id:
            return False

        content = memory.get("content")

        if not content:
            key = memory.get("key", "")
            value = memory.get("value", "")
            content = f"{key}: {value}"

        if not isinstance(content, str):
            return False

        if not content.strip():
            return False

        vector = self.embedding_model.embed(
            content
        )

        if not vector:
            return False

        return self.vector_store.add(
            memory_id,
            vector,
        )

    # ========================================================
    # Index many memories
    # ========================================================

    def index_memories(self, memories):
        """
        Create embeddings for multiple memories.

        Returns:
            Number of successfully indexed memories.
        """

        if not memories:
            return 0

        count = 0

        for memory in memories:
            if self.index_memory(memory):
                count += 1

        return count

    # ========================================================
    # Remove memory
    # ========================================================

    def remove_memory(self, memory_id):
        """
        Remove a memory from the vector index.
        """

        return self.vector_store.delete(
            memory_id
        )

    # ========================================================
    # Search
    # ========================================================

    def search(
        self,
        query,
        limit=8,
        min_similarity=0.0,
    ):
        """
        Search memories using semantic similarity.

        Args:
            query:
                Search text.

            limit:
                Maximum number of results.

            min_similarity:
                Minimum cosine similarity required.

        Returns:
            [
                {
                    "memory_id": "...",
                    "similarity": 0.95,
                }
            ]
        """

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        if limit <= 0:
            return []

        try:
            min_similarity = float(
                min_similarity
            )
        except (TypeError, ValueError):
            min_similarity = 0.0

        vector = self.embedding_model.embed(
            query
        )

        if not vector:
            return []

        results = self.vector_store.search(
            vector,
            limit=limit,
        )

        if not results:
            return []

        filtered = []

        for result in results:
            similarity = float(
                result.get(
                    "similarity",
                    0.0,
                )
            )

            if similarity < min_similarity:
                continue

            filtered.append(result)

        return filtered

    # ========================================================
    # Get vector
    # ========================================================

    def get_vector(self, memory_id):
        return self.vector_store.get(
            memory_id
        )

    # ========================================================
    # Clear
    # ========================================================

    def clear(self):
        self.vector_store.clear()

    # ========================================================
    # Length
    # ========================================================

    def __len__(self):
        return len(self.vector_store)