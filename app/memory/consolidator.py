# Phase 5.2 — Memory Consolidation


class MemoryConsolidator:
    """
    Consolidate related memories into a stronger memory representation.
    """

    def __init__(self, store, graph=None):
        self.store = store
        self.graph = graph

    def consolidate(self, memory_ids):
        """
        Consolidate multiple memories into one logical memory.

        Returns:
            memory_id of the new consolidated memory,
            or None if consolidation cannot be performed.
        """

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not memory_ids:
            return None

        memories = []

        for memory_id in memory_ids:
            memory = self.store.get_memory(memory_id)

            if memory:
                memories.append(memory)

        # Need at least two memories to consolidate
        if len(memories) < 2:
            return None

        # ----------------------------------------------------
        # Combine keys
        # ----------------------------------------------------

        keys = [
            str(memory.get("key", "")).strip()
            for memory in memories
            if memory.get("key")
        ]

        # ----------------------------------------------------
        # Combine values
        # ----------------------------------------------------

        values = [
            str(memory.get("value", "")).strip()
            for memory in memories
            if memory.get("value")
        ]

        # ----------------------------------------------------
        # Merge tags
        # ----------------------------------------------------

        tags = set()

        for memory in memories:
            tags.update(
                str(item).strip()
                for item in memory.get("tags", [])
                if item
            )

        # ----------------------------------------------------
        # Merge entities
        # ----------------------------------------------------

        entities = set()

        for memory in memories:
            entities.update(
                str(item).strip()
                for item in memory.get("entities", [])
                if item
            )

        # ----------------------------------------------------
        # Source memory IDs
        # ----------------------------------------------------

        source_memory_ids = [
            memory.get("memory_id")
            for memory in memories
            if memory.get("memory_id")
        ]

        # ----------------------------------------------------
        # Determine metadata
        # ----------------------------------------------------

        memory_type = memories[0].get(
            "memory_type",
            "fact",
        )

        subject = memories[0].get(
            "subject",
            "user",
        )

        source = "consolidation"

        # Use strongest importance/confidence
        importance = max(
            float(memory.get("importance", 0.0))
            for memory in memories
        )

        confidence = min(
            float(memory.get("confidence", 0.0))
            for memory in memories
        )

        # ----------------------------------------------------
        # Build consolidated value
        # ----------------------------------------------------

        consolidated_value = " | ".join(
            dict.fromkeys(values)
        )

        # ----------------------------------------------------
        # Build relationship metadata
        # ----------------------------------------------------

        relationships = [
            {
                "type": "consolidated_from",
                "memory_id": memory_id,
            }
            for memory_id in source_memory_ids
        ]

        # ----------------------------------------------------
        # Create new memory
        # ----------------------------------------------------

        consolidated_memory_id = self.store.add_memory(
            memory_type=memory_type,
            subject=subject,
            key=keys[0] if keys else "consolidated_memory",
            value=consolidated_value,
            importance=importance,
            confidence=confidence,
            source=source,
            tags=sorted(tags),
            entities=sorted(entities),
            relationships=relationships,
        )

        return consolidated_memory_id