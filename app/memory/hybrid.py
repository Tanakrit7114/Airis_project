# Phase 2.3 — Hybrid Retrieval

from app.memory.ranking import MemoryRanker


class HybridMemoryRetriever:
    """
    Hybrid memory retrieval.

    Combines:
        - Memory relevance
        - Memory ranking
        - Importance
        - Confidence
        - Access frequency
        - Decay
    """

    def __init__(self, ranker=None):
        self.ranker = ranker or MemoryRanker()

    def retrieve(
        self,
        query,
        memories,
        limit=None,
    ):
        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        if not memories:
            return []

        effective_limit = (
            len(memories)
            if limit is None
            else limit
        )

        ranked = self.ranker.rank(
            query,
            memories,
            limit=effective_limit,
        )


        if not ranked:
            return []

        return ranked[:limit]
