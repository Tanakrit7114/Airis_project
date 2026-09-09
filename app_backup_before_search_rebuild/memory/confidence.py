# Phase 1.1 — Memory 2.0
# app/memory/confidence.py

class ConfidenceScorer:
    """
    Calculate how confident JARVIS should be about a memory.

    Confidence is different from importance:
        - importance = how important the memory is
        - confidence = how reliable the memory is
    """

    def __init__(self, default=0.8):
        self.default = self._clamp(default)

    @staticmethod
    def _clamp(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = 0.8

        return max(0.0, min(1.0, value))

    @staticmethod
    def _text(memory):
        if not memory:
            return ""

        parts = [
            memory.get("content"),
            memory.get("value"),
        ]

        return " ".join(
            str(part)
            for part in parts
            if part is not None
        ).strip()

    def score(self, memory=None):
        """
        Return a confidence score between 0.0 and 1.0.
        """

        if not memory:
            return self.default

        # Explicit confidence takes priority.
        if "confidence" in memory:
            return self._clamp(
                memory.get("confidence")
            )

        score = self.default

        text = self._text(memory).lower()

        # Strong statements are generally more reliable.
        strong_markers = (
            "is ",
            "am ",
            "are ",
            "my ",
            "i use ",
            "i like ",
            "i prefer ",
            "i have ",
            "i study ",
            "i work ",
        )

        # Uncertainty markers reduce confidence.
        uncertain_markers = (
            "maybe",
            "might",
            "perhaps",
            "probably",
            "possibly",
            "i think",
            "not sure",
            "i'm not sure",
            "i am not sure",
            "could be",
            "guess",
        )

        if any(marker in text for marker in strong_markers):
            score += 0.10

        if any(marker in text for marker in uncertain_markers):
            score -= 0.30

        # Direct user statements are generally stronger
        # than inferred memories.
        source = str(
            memory.get("source", "")
        ).lower()

        if source in {
            "user",
            "conversation",
            "explicit",
        }:
            score += 0.05

        if source in {
            "inference",
            "inferred",
            "model",
        }:
            score -= 0.15

        return self._clamp(score)

    def calculate(self, memory=None):
        """
        Alias for score().
        """
        return self.score(memory)

    def update(self, memory, confidence=None):
        """
        Return a copy of the memory with an updated
        confidence value.
        """

        if memory is None:
            return None

        result = dict(memory)

        if confidence is None:
            confidence = self.score(result)

        result["confidence"] = self._clamp(
            confidence
        )

        return result
