# Phase 1.1 — Memory 2.0
# app/memory/access_tracker.py

from datetime import datetime, timezone


class MemoryAccessTracker:
    """
    Tracks how often a memory is accessed and
    when it was last accessed.
    """

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def record_access(self, memory):
        """
        Return a copy of the memory with updated
        access_count and last_accessed.
        """

        if not isinstance(memory, dict):
            return None

        result = memory.copy()

        try:
            count = int(
                result.get("access_count", 0)
            )
        except (TypeError, ValueError):
            count = 0

        result["access_count"] = count + 1
        result["last_accessed"] = self._now()

        return result

    def get_access_count(self, memory):
        """
        Return the number of times a memory
        has been accessed.
        """

        if not isinstance(memory, dict):
            return 0

        try:
            return max(
                0,
                int(
                    memory.get(
                        "access_count",
                        0,
                    )
                ),
            )
        except (TypeError, ValueError):
            return 0

    def get_last_accessed(self, memory):
        """
        Return the last_accessed timestamp.
        """

        if not isinstance(memory, dict):
            return None

        return memory.get("last_accessed")

    def track_memory_access(self, memory):
        """
        Alias for record_access().
        """

        return self.record_access(memory)

    def access_score(self, memory):
        """
        Calculate a normalized access score.

        More accesses produce a higher score,
        but the score is capped at 1.0.
        """

        count = self.get_access_count(memory)

        return min(
            1.0,
            count / 10.0,
        )
