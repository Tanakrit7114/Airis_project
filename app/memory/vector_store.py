# Phase 3.3 — Memory Vector Store

import math


class MemoryVectorStore:
    """
    Store and search memory embeddings in memory.

    Each vector is associated with a memory_id.

    Search uses cosine similarity.
    """

    def __init__(self):
        self._vectors = {}

    def add(self, memory_id, vector):
        """
        Add or replace a vector for a memory.
        """
        if memory_id is None:
            return False

        if not vector:
            return False

        try:
            values = [float(value) for value in vector]
        except (TypeError, ValueError):
            return False

        if not values:
            return False

        self._vectors[str(memory_id)] = values

        return True

    def get(self, memory_id):
        """
        Return the vector for a memory, or None.
        """
        if memory_id is None:
            return None

        vector = self._vectors.get(str(memory_id))

        if vector is None:
            return None

        return list(vector)

    def delete(self, memory_id):
        """
        Delete a memory vector.
        """
        if memory_id is None:
            return False

        memory_id = str(memory_id)

        if memory_id not in self._vectors:
            return False

        del self._vectors[memory_id]

        return True

    def clear(self):
        """
        Remove all stored vectors.
        """
        self._vectors.clear()

    def __len__(self):
        return len(self._vectors)

    def _cosine_similarity(self, a, b):
        """
        Calculate cosine similarity between two vectors.
        """
        if not a or not b:
            return 0.0

        if len(a) != len(b):
            return 0.0

        dot = sum(
            x * y
            for x, y in zip(a, b)
        )

        norm_a = math.sqrt(
            sum(x * x for x in a)
        )

        norm_b = math.sqrt(
            sum(y * y for y in b)
        )

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot / (norm_a * norm_b)

    def search(self, query_vector, limit=8):
        """
        Search for the most similar memory vectors.

        Returns:

            [
                {
                    "memory_id": "...",
                    "similarity": 0.95,
                }
            ]
        """
        if not query_vector:
            return []

        if limit <= 0:
            return []

        try:
            query = [
                float(value)
                for value in query_vector
            ]
        except (TypeError, ValueError):
            return []

        if not query:
            return []

        results = []

        for memory_id, vector in self._vectors.items():
            similarity = self._cosine_similarity(
                query,
                vector,
            )

            results.append(
                {
                    "memory_id": memory_id,
                    "similarity": similarity,
                }
            )

        results.sort(
            key=lambda item: item["similarity"],
            reverse=True,
        )

        return results[:limit]
