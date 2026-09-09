# Phase 3.8 — Memory Relevance / Reranking

from app.memory.hybrid_retrieval import HybridMemoryRetriever


class MemoryReranker:
    """
    Re-rank retrieved memories using:

        Hybrid Score
             +
        Importance
             +
        Confidence
             ↓
        Relevance Score
    """

    def __init__(self, retriever=None):
        self.retriever = (
            retriever
            if retriever is not None
            else HybridMemoryRetriever()
        )

    def rerank(
        self,
        query,
        limit=5,
        min_similarity=0.0,
    ):
        """
        Retrieve memories and rank them by overall relevance.
        """

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        if limit <= 0:
            return []

        results = self.retriever.search(
            query,
            limit=max(limit, 8),
            min_similarity=min_similarity,
        )

        if not results:
            return []

        ranked = []

        for memory in results:
            hybrid_score = float(
                memory.get("hybrid_score", 0.0)
            )

            importance = float(
                memory.get("importance", 0.0)
            )

            confidence = float(
                memory.get("confidence", 0.0)
            )

            # Relevance combines retrieval quality
            # with memory quality.
            relevance_score = (
                0.7 * hybrid_score
                + 0.15 * importance
                + 0.15 * confidence
            )

            result = dict(memory)

            result["relevance_score"] = (
                relevance_score
            )

            ranked.append(result)

        ranked.sort(
            key=lambda item: (
                item["relevance_score"],
                item.get("hybrid_score", 0.0),
                item.get("similarity", 0.0),
                item.get("exact_score", 0.0),
            ),
            reverse=True,
        )

        return ranked[:limit]

    def best_reranked(
        self,
        query,
        min_similarity=0.0,
    ):
        """
        Return the single most relevant memory.
        """

        results = self.rerank(
            query,
            limit=1,
            min_similarity=min_similarity,
        )

        if not results:
            return None

        return results[0]
