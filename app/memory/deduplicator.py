class MemoryDeduplicator:
    """
    Detect whether a memory already exists.

    Duplicate identity:
    - memory_type
    - subject
    - key
    - normalized value
    """

    def _normalize(self, value):
        if value is None:
            return ""

        return " ".join(
            str(value)
            .strip()
            .lower()
            .split()
        )

    def is_duplicate(self, new_memory, existing_memories):
        """
        Return True if new_memory is already represented
        by an existing memory.
        """

        new_type = self._normalize(
            new_memory.get("memory_type")
        )

        new_subject = self._normalize(
            new_memory.get("subject")
        )

        new_key = self._normalize(
            new_memory.get("key")
        )

        new_value = self._normalize(
            new_memory.get("value")
        )

        for memory in existing_memories:

            old_type = self._normalize(
                memory.get("memory_type")
            )

            old_subject = self._normalize(
                memory.get("subject")
            )

            old_key = self._normalize(
                memory.get("key")
            )

            old_value = self._normalize(
                memory.get("value")
            )

            if (
                new_type == old_type
                and new_subject == old_subject
                and new_key == old_key
                and new_value == old_value
            ):
                return True

        return False

    def filter_duplicates(
        self,
        memories,
        existing_memories,
    ):
        """
        Remove memories that already exist.

        Returns:
            list of new, non-duplicate memories
        """

        result = []

        known = list(existing_memories)

        for memory in memories:

            if self.is_duplicate(
                memory,
                known,
            ):
                continue

            result.append(memory)

            # Prevent duplicates inside the same batch
            known.append(memory)

        return result
    
    def deduplicate(self, memories):
        """
        Remove duplicate memories while preserving order.
        """
        if not memories:
            return []

        result = []

        for memory in memories:
            if not isinstance(memory, dict):
                continue

            duplicate = False

            for existing in result:
                if self.is_duplicate(memory, existing):
                    duplicate = True
                    break

            if not duplicate:
                result.append(memory)

        return result
