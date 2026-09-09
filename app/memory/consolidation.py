# Phase 1.1 — Memory 2.0
# app/memory/consolidation.py


class MemoryConsolidator:

    def __init__(self, similarity_threshold=0.8):
        self.similarity_threshold = similarity_threshold

    def _normalize(self, value):
        if value is None:
            return ""

        return " ".join(
            str(value).strip().lower().split()
        )

    def _memory_signature(self, memory):
        if not isinstance(memory, dict):
            return None

        return (
            self._normalize(memory.get("memory_type")),
            self._normalize(memory.get("subject")),
            self._normalize(memory.get("key")),
        )

    def are_related(self, memory_a, memory_b):
        """
        Determine whether two memories belong to
        the same logical topic.
        """

        if not isinstance(memory_a, dict):
            return False

        if not isinstance(memory_b, dict):
            return False

        signature_a = self._memory_signature(memory_a)
        signature_b = self._memory_signature(memory_b)

        if signature_a == signature_b:
            return True

        return False

    def consolidate(self, memories):
        """
        Group related memories together.

        Returns:
            list[list[dict]]
        """

        if not memories:
            return []

        groups = []

        for memory in memories:

            if not isinstance(memory, dict):
                continue

            placed = False

            for group in groups:

                if self.are_related(
                    memory,
                    group[0],
                ):
                    group.append(memory)
                    placed = True
                    break

            if not placed:
                groups.append([memory])

        return groups

    def merge_group(self, memories):
        """
        Merge a group of related memories into one memory.

        The newest / most recently updated memory is preferred
        when available.
        """

        if not memories:
            return None

        valid = [
            memory
            for memory in memories
            if isinstance(memory, dict)
        ]

        if not valid:
            return None

        # Start from the highest-importance memory.
        merged = max(
            valid,
            key=lambda memory: float(
                memory.get("importance", 0.0)
            ),
        ).copy()

        values = []

        for memory in valid:

            value = memory.get("value")

            if value is None:
                continue

            value = str(value).strip()

            if value and value not in values:
                values.append(value)

        # Preserve a single value when possible.
        if len(values) == 1:
            merged["value"] = values[0]

        elif values:
            merged["value"] = "; ".join(values)

        key = merged.get("key")

        if key and merged.get("value"):
            merged["content"] = (
                f"{key}: {merged['value']}"
            )

        return merged

    def consolidate_and_merge(self, memories):
        """
        Group related memories and merge each group.

        Returns:
            list[dict]
        """

        groups = self.consolidate(memories)

        return [
            self.merge_group(group)
            for group in groups
            if self.merge_group(group) is not None
        ]
