# Phase 1.1 — Memory 2.0
# app/memory/importance.py


class ImportanceScorer:

    def __init__(self):
        pass

    def score(self, memory):
        """
        Calculate memory importance score from 0.0 to 1.0.
        """

        if not isinstance(memory, dict):
            return 0.0

        score = 0.5

        memory_type = str(
            memory.get("memory_type", "")
        ).lower()

        content = str(
            memory.get("content")
            or memory.get("value")
            or ""
        ).lower()

        # Memory type weighting
        type_weights = {
            "profile": 0.20,
            "preference": 0.15,
            "project": 0.15,
            "task": 0.10,
            "relationship": 0.10,
            "semantic": 0.05,
            "episodic": 0.00,
        }

        score += type_weights.get(
            memory_type,
            0.0,
        )

        # Important keywords
        important_keywords = [
            "always",
            "never",
            "important",
            "favorite",
            "prefer",
            "goal",
            "project",
            "deadline",
            "must",
            "remember",
        ]

        matches = sum(
            1
            for keyword in important_keywords
            if keyword in content
        )

        score += min(
            matches * 0.05,
            0.20,
        )

        # Explicit importance supplied by caller
        if "importance" in memory:
            try:
                explicit = float(
                    memory["importance"]
                )

                # Blend existing importance with
                # calculated score.
                score = (
                    explicit * 0.5
                    + score * 0.5
                )

            except (
                TypeError,
                ValueError,
            ):
                pass

        return max(
            0.0,
            min(1.0, score),
        )

    def score_and_update(self, memory):
        """
        Calculate importance and return a copy
        containing the new score.
        """

        if not isinstance(memory, dict):
            return None

        result = memory.copy()

        result["importance"] = self.score(
            result
        )

        return result
