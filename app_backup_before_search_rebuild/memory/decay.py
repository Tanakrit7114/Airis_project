# Phase 1.1 — Memory 2.0
# app/memory/decay.py

from datetime import datetime, timezone


class MemoryDecay:

    def __init__(
        self,
        default_decay_rate=0.01,
        minimum_score=0.0,
    ):
        self.default_decay_rate = float(
            default_decay_rate
        )
        self.minimum_score = float(
            minimum_score
        )

    def _clamp(self, value):
        return max(
            self.minimum_score,
            min(1.0, float(value)),
        )

    def _parse_datetime(self, value):
        """
        Convert a datetime value into a datetime object.
        """

        if isinstance(value, datetime):
            dt = value

        elif not value:
            return None

        else:
            try:
                dt = datetime.fromisoformat(
                    str(value).replace(
                        "Z",
                        "+00:00",
                    )
                )
            except ValueError:
                return None

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt

    def calculate(
        self,
        importance,
        age_days,
        decay_rate=None,
    ):
        """
        Calculate decayed importance.

        Formula:

            score = importance * e^(-decay_rate * age_days)

        """

        importance = self._clamp(
            importance
        )

        age_days = max(
            0.0,
            float(age_days),
        )

        if decay_rate is None:
            decay_rate = (
                self.default_decay_rate
            )

        decay_rate = max(
            0.0,
            float(decay_rate),
        )

        # Avoid importing math at module level
        # unless calculation is actually needed.
        import math

        score = importance * math.exp(
            -decay_rate * age_days
        )

        return self._clamp(score)

    def age_days(
        self,
        last_accessed,
        now=None,
    ):
        """
        Calculate how many days have passed
        since the memory was accessed.
        """

        accessed = self._parse_datetime(
            last_accessed
        )

        if accessed is None:
            return 0.0

        current = (
            self._parse_datetime(now)
            if now is not None
            else datetime.now(timezone.utc)
        )

        seconds = (
            current - accessed
        ).total_seconds()

        return max(
            0.0,
            seconds / 86400.0,
        )

    def decay_memory(
        self,
        memory,
        now=None,
    ):
        """
        Return a copy of the memory with
        calculated decayed importance.
        """

        if not isinstance(memory, dict):
            return None

        result = memory.copy()

        importance = result.get(
            "importance",
            0.5,
        )

        last_accessed = result.get(
            "last_accessed"
        )

        age = self.age_days(
            last_accessed,
            now=now,
        )

        decay_rate = result.get(
            "decay_rate",
            self.default_decay_rate,
        )

        result["importance"] = self.calculate(
            importance=importance,
            age_days=age,
            decay_rate=decay_rate,
        )

        return result

    def is_expired(
        self,
        memory,
        now=None,
    ):
        """
        Check whether a memory has passed
        its expires_at timestamp.
        """

        if not isinstance(memory, dict):
            return False

        expires_at = self._parse_datetime(
            memory.get("expires_at")
        )

        if expires_at is None:
            return False

        current = (
            self._parse_datetime(now)
            if now is not None
            else datetime.now(timezone.utc)
        )

        return current >= expires_at
