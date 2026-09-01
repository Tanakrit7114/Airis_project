# Phase 3.6 — Memory Ranking


class MemoryRanker:
    """
    Score and rank memories based on:
        - relevance
        - importance
        - confidence
        - access frequency
        - decay

    This class MUST NOT import HybridMemoryRetriever.
    """

    # ========================================================
    # Public scoring
    # ========================================================

    def score(self, query, memory):
        """
        Return a normalized memory score between 0.0 and 1.0.
        """

        if not isinstance(query, str):
            return 0.0

        query = query.strip()

        if not query:
            return 0.0

        if not isinstance(memory, dict):
            return 0.0

        relevance = self._relevance(
            query,
            memory,
        )

        importance = self._importance(
            memory,
        )

        confidence = self._confidence(
            memory,
        )

        access = self._access(
            memory,
        )

        decay = self._decay(
            memory,
        )

        return (
            0.50 * relevance
            + 0.20 * importance
            + 0.15 * confidence
            + 0.10 * access
            + 0.05 * decay
        )

    # ========================================================
    # Relevance
    # ========================================================

    def _relevance(self, query, memory):
        """
        Measure lexical relevance between query and memory.
        """

        if not isinstance(query, str):
            return 0.0

        if not isinstance(memory, dict):
            return 0.0

        query = query.strip().lower()

        if not query:
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

        # Exact full match
        if query == key:
            return 1.0

        if query == value:
            return 1.0

        # Query appears directly
        if query in key:
            return 0.95

        if query in value:
            return 0.90

        if query in content:
            return 0.80

        # Word overlap
        query_words = set(
            query.replace("_", " ").split()
        )

        searchable_words = set(
            searchable
            .replace("_", " ")
            .split()
        )

        if not query_words:
            return 0.0

        overlap = (
            query_words
            & searchable_words
        )

        return (
            len(overlap)
            / len(query_words)
        )

    # ========================================================
    # Importance
    # ========================================================

    def _importance(self, memory):
        """
        Return normalized importance.
        """

        if not isinstance(memory, dict):
            return 0.0

        value = self._safe_float(
            memory.get(
                "importance",
                0.0,
            )
        )

        return max(
            0.0,
            min(1.0, value),
        )

    # ========================================================
    # Confidence
    # ========================================================

    def _confidence(self, memory):
        """
        Return normalized confidence.
        """

        if not isinstance(memory, dict):
            return 0.0

        value = self._safe_float(
            memory.get(
                "confidence",
                0.0,
            )
        )

        return max(
            0.0,
            min(1.0, value),
        )

    # ========================================================
    # Access frequency
    # ========================================================

    def _access(self, memory):
        """
        Convert access_count into a normalized score.

        Uses logarithmic scaling so frequently accessed
        memories gain importance without dominating ranking.
        """

        if not isinstance(memory, dict):
            return 0.0

        access_count = self._safe_float(
            memory.get(
                "access_count",
                0,
            )
        )

        if access_count <= 0:
            return 0.0

        import math

        return min(
            1.0,
            math.log1p(access_count)
            / math.log1p(20),
        )

    # ========================================================
    # Decay
    # ========================================================

    def _decay(self, memory):
        """
        Convert decay_rate into a quality score.

        Higher decay rate means lower score.
        """

        if not isinstance(memory, dict):
            return 0.0

        decay_rate = self._safe_float(
            memory.get(
                "decay_rate",
                0.0,
            )
        )

        decay_rate = max(
            0.0,
            min(1.0, decay_rate),
        )

        return 1.0 - decay_rate

    # ========================================================
    # Rank
    # ========================================================

    def rank(
        self,
        query,
        memories,
        limit=None,
    ):
        """
        Rank a list of memories.

        Returns copies of the original memories with
        a ranking score attached.
        """

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        if not isinstance(memories, list):
            return []

        if not memories:
            return []

        if limit is not None:
            try:
                limit = int(limit)
            except (
                TypeError,
                ValueError,
            ):
                return []

            if limit <= 0:
                return []

        ranked = []

        for memory in memories:
            if not isinstance(memory, dict):
                continue

            result = dict(memory)

            result["ranking_score"] = (
                self.score(
                    query,
                    memory,
                )
            )

            ranked.append(result)

        ranked.sort(
            key=lambda item: (
                item.get(
                    "ranking_score",
                    0.0,
                ),
                self._relevance(
                    query,
                    item,
                ),
                self._importance(
                    item,
                ),
                self._confidence(
                    item,
                ),
                self._access(
                    item,
                ),
                self._decay(
                    item,
                ),
            ),
            reverse=True,
        )

        if limit is not None:
            return ranked[:limit]

        return ranked

    # ========================================================
    # Safe float
    # ========================================================

    @staticmethod
    def _safe_float(value):
        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0