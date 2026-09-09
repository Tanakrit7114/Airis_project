# Phase 1.1 — Memory 2.0
# app/memory/contradiction.py


class ContradictionDetector:

    def _normalize(self, value):
        """
        Normalize values before comparison.
        """
        if value is None:
            return ""

        return str(value).strip().lower()

    def detect(self, new_memory, existing_memories):
        """
        Return all existing memories that contradict new_memory.
        """
        contradictions = []

        if not isinstance(new_memory, dict):
            return contradictions

        for memory in existing_memories or []:

            if not isinstance(memory, dict):
                continue

            if (
                memory.get("memory_type") == new_memory.get("memory_type")
                and memory.get("subject") == new_memory.get("subject")
                and memory.get("key") == new_memory.get("key")
                and self._normalize(memory.get("value"))
                != self._normalize(new_memory.get("value"))
            ):
                contradictions.append(memory)

        return contradictions

    def is_contradiction(self, new_memory, existing_memory):
        """
        Check whether new_memory contradicts an existing memory.

        existing_memory may be:
        - a single memory dict
        - a list of memory dicts
        """

        if not isinstance(new_memory, dict):
            return False

        if not existing_memory:
            return False

        # Support a list of existing memories
        if isinstance(existing_memory, list):

            return any(
                self.is_contradiction(
                    new_memory,
                    memory,
                )
                for memory in existing_memory
            )

        # Support a single memory dict
        if not isinstance(existing_memory, dict):
            return False

        return (
            new_memory.get("memory_type")
            == existing_memory.get("memory_type")
            and
            new_memory.get("subject")
            == existing_memory.get("subject")
            and
            new_memory.get("key")
            == existing_memory.get("key")
            and
            self._normalize(new_memory.get("value"))
            != self._normalize(existing_memory.get("value"))
        )

    def find_contradictions(self, new_memory, existing_memories):
        """
        Return all memories that contradict new_memory.
        """

        return self.detect(
            new_memory,
            existing_memories,
        )