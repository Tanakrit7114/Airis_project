# Phase 1.1 — Memory 2.0
# app/memory/relationship.py


class RelationshipTracker:
    """
    Manage relationships between memories/entities.

    Relationship format:

    {
        "type": "uses",
        "source": "JARVIS",
        "target": "Python"
    }
    """

    VALID_FIELDS = {
        "type",
        "source",
        "target",
    }

    def _normalize(self, value):
        if value is None:
            return ""

        return str(value).strip()

    def _normalize_relationship(self, relationship):
        if not isinstance(relationship, dict):
            return None

        relationship_type = self._normalize(
            relationship.get("type")
        )
        source = self._normalize(
            relationship.get("source")
        )
        target = self._normalize(
            relationship.get("target")
        )

        if not relationship_type:
            return None

        if not source or not target:
            return None

        return {
            "type": relationship_type,
            "source": source,
            "target": target,
        }

    def add_relationship(
        self,
        memory,
        relationship,
    ):
        """
        Add a relationship to a memory.

        Duplicate relationships are ignored.
        """

        if not isinstance(memory, dict):
            return None

        normalized = self._normalize_relationship(
            relationship
        )

        if normalized is None:
            return memory.copy()

        result = memory.copy()

        relationships = result.get(
            "relationships",
            [],
        )

        if not isinstance(relationships, list):
            relationships = []

        normalized_relationships = []

        for item in relationships:
            normalized_item = (
                self._normalize_relationship(item)
            )

            if normalized_item is not None:
                normalized_relationships.append(
                    normalized_item
                )

        if normalized not in normalized_relationships:
            normalized_relationships.append(
                normalized
            )

        result["relationships"] = (
            normalized_relationships
        )

        return result

    def remove_relationship(
        self,
        memory,
        relationship,
    ):
        """
        Remove a relationship from a memory.
        """

        if not isinstance(memory, dict):
            return None

        normalized = self._normalize_relationship(
            relationship
        )

        result = memory.copy()

        relationships = result.get(
            "relationships",
            [],
        )

        if not isinstance(relationships, list):
            relationships = []

        result["relationships"] = [
            item
            for item in relationships
            if self._normalize_relationship(item)
            != normalized
        ]

        return result

    def get_relationships(self, memory):
        """
        Return all valid relationships.
        """

        if not isinstance(memory, dict):
            return []

        relationships = memory.get(
            "relationships",
            [],
        )

        if not isinstance(relationships, list):
            return []

        result = []

        for item in relationships:
            normalized = (
                self._normalize_relationship(item)
            )

            if normalized is not None:
                result.append(normalized)

        return result

    def find_related_memories(
        self,
        memory,
        memories,
    ):
        """
        Find memories connected to the given memory.

        A memory is considered related when its
        memory_id appears as a relationship source
        or target.
        """

        if not isinstance(memory, dict):
            return []

        if not isinstance(memories, list):
            return []

        memory_id = memory.get("memory_id")

        if not memory_id:
            return []

        relationships = self.get_relationships(
            memory
        )

        related_ids = set()

        for relationship in relationships:
            source = relationship["source"]
            target = relationship["target"]

            if source == memory_id:
                related_ids.add(target)

            if target == memory_id:
                related_ids.add(source)

        result = []

        for candidate in memories:
            if not isinstance(candidate, dict):
                continue

            candidate_id = candidate.get(
                "memory_id"
            )

            if candidate_id in related_ids:
                result.append(candidate)

        return result

    def has_relationship(
        self,
        memory,
        relationship,
    ):
        """
        Check whether a memory contains
        a specific relationship.
        """

        normalized = self._normalize_relationship(
            relationship
        )

        if normalized is None:
            return False

        return normalized in self.get_relationships(
            memory
        )
