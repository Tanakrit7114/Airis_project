# Phase 2.2 — Memory Ranking
# app/memory/ranking.py

import math


class MemoryRanker:
    """
    Rank retrieved memories by relevance and memory quality.
    """

    def _tokenize(self, text):
        if not isinstance(text, str):
            return set()

        return {
            token.lower()
            for token in text.replace("_", " ").split()
            if token
        }

    def _relevance(self, query, memory):
        query_tokens = self._tokenize(query)

        if not query_tokens:
            return 0.0

        text = " ".join(
            [
                str(memory.get("memory_type", "")),
                str(memory.get("subject", "")),
                str(memory.get("key", "")).replace("_", " "),
                str(memory.get("value", "")),
            ]
        ).lower()

        text_tokens = self._tokenize(text)

        if not text_tokens:
            return 0.0

        matched = query_tokens.intersection(text_tokens)

        score = len(matched) / len(query_tokens)

        # Exact phrase match gets a strong bonus.
        if query.lower() in text:
            score += 1.0

        return score

    def _importance(self, memory):
        return max(
            0.0,
            min(
                1.0,
                float(memory.get("importance", 0.5)),
            ),
        )

    def _confidence(self, memory):
        return max(
            0.0,
            min(
                1.0,
                float(memory.get("confidence", 0.8)),
            ),
        )

    def _access(self, memory):
        count = max(
            0,
            int(memory.get("access_count", 0)),
        )

        # Logarithmic scaling prevents frequently accessed
        # memories from dominating the ranking.
        return min(
            1.0,
            math.log1p(count) / math.log1p(20),
        )

    def _decay(self, memory):
        return max(
            0.0,
            min(
                1.0,
                float(memory.get("decay_rate", 0.0)),
            ),
        )

    def score(self, query, memory):
        """
        Calculate ranking score for one memory.
        """

        relevance = self._relevance(
            query,
            memory,
        )

        importance = self._importance(memory)
        confidence = self._confidence(memory)
        access = self._access(memory)
        decay = self._decay(memory)

        score = (
            relevance * 5.0
            + importance * 2.0
            + confidence * 1.5
            + access * 1.0
            - decay * 5.0
        )

        return score

    def rank(
        self,
        query,
        memories,
        limit=8,
    ):
        """
        Rank memories from most relevant to least relevant.
        """

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        if not memories:
            return []

        if limit <= 0:
            return []

        ranked = []

        for memory in memories:
            score = self.score(
                query,
                memory,
            )

            item = dict(memory)
            item["ranking_score"] = score

            ranked.append(item)

        ranked.sort(
            key=lambda memory: memory["ranking_score"],
            reverse=True,
        )

        return ranked[:limit]

    def rank_one(self, query, memories):
        """
        Return the highest-ranked memory,
        or None when nothing is available.
        """

        result = self.rank(
            query,
            memories,
            limit=1,
        )

        return result[0] if result else None
