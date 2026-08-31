# Phase 3.6 — Memory Ranking


class MemoryRanker:
    """
    Score a memory based on relevance and memory quality.

    This class MUST NOT import HybridMemoryRetriever.
    """

    def score(self, query, memory):
        if not isinstance(query, str):
            return 0.0

        query = query.strip().lower()

        if not query:
            return 0.0

        if not isinstance(memory, dict):
            return 0.0

        key = str(
            memory.get("key", "")
        ).lower()

        value = str(
            memory.get("value", "")
        ).lower()

        content = str(
            memory.get("content", "")
        ).lower()

        searchable = (
            f"{key} {value} {content}"
        )

        query_words = set(
            query.split()
        )

        if not query_words:
            return 0.0

        searchable_words = set(
            searchable.split()
        )

        overlap = (
            query_words
            & searchable_words
        )

        keyword_score = (
            len(overlap)
            / len(query_words)
        )

        importance = self._safe_float(
            memory.get("importance", 0.0)
        )

        confidence = self._safe_float(
            memory.get("confidence", 0.0)
        )

        return (
            0.6 * keyword_score
            + 0.2 * importance
            + 0.2 * confidence
        )

    @staticmethod
    def _safe_float(value):
        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0