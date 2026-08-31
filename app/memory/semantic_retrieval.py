# Phase 3.6 — Semantic Memory Retrieval

from app.memory.store import MemoryStore
from app.memory.vector_index import MemoryVectorIndex


class SemanticMemoryRetriever:
    """
    Retrieve memories using semantic vector similarity.

    Flow:

        Query
          ↓
        Embedding
          ↓
        Vector Search
          ↓
        memory_id
          ↓
        MemoryStore
          ↓
        Memory
    """

    def __init__(
        self,
        store=None,
        vector_index=None,
    ):
        self.store = store if store is not None else MemoryStore()

        self.vector_index = (
            vector_index
            if vector_index is not None
            else MemoryVectorIndex()
        )

    # ========================================================
    # Search
    # ========================================================

    def search(
        self,
        query,
        limit=5,
        min_similarity=0.0,
    ):
        """
        Search memories semantically.
        """

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        if limit <= 0:
            return []

        # ----------------------------------------------------
        # Vector search
        # ----------------------------------------------------

        results = self.vector_index.search(
            query,
            limit=limit,
        )

        if not results:
            return []

        memories = []

        # ----------------------------------------------------
        # Resolve vector results → MemoryStore
        # ----------------------------------------------------

        for result in results:

            if not isinstance(result, dict):
                continue

            similarity = result.get(
                "similarity",
                0.0,
            )

            try:
                similarity = float(similarity)
            except (TypeError, ValueError):
                continue

            if similarity < min_similarity:
                continue

            memory_id = result.get(
                "memory_id"
            )

            if memory_id is None:
                continue

            # ------------------------------------------------
            # Primary lookup
            # ------------------------------------------------

            memory = self.store.get_memory(
                memory_id
            )

            # ------------------------------------------------
            # Fallback:
            # Some MemoryStore implementations may return
            # string/integer IDs differently.
            # ------------------------------------------------

            if not memory:
                memory = self.store.get_memory(
                    str(memory_id)
                )

            if not memory:
                continue

            memory = dict(memory)

            memory["similarity"] = similarity

            memories.append(memory)

        return memories

    # ========================================================
    # Best memory
    # ========================================================

    def best(
        self,
        query,
        min_similarity=0.0,
    ):
        """
        Return the single best matching memory.
        """

        results = self.search(
            query,
            limit=1,
            min_similarity=min_similarity,
        )

        if not results:
            return None

        return results[0]