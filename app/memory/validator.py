class MemoryValidator:
    """
    Validate memory objects before they are stored.

    Responsibilities:
    - Validate required fields
    - Validate memory_type
    - Validate score ranges
    - Validate list fields
    - Normalize values
    """

    VALID_MEMORY_TYPES = {
        "episodic",
        "semantic",
        "preference",
        "profile",
        "project",
        "relationship",
        "task",
        "fact",
        "education",
    }

    REQUIRED_FIELDS = {
        "memory_type",
        "subject",
        "key",
        "value",
    }

    LIST_FIELDS = {
        "tags",
        "entities",
        "relationships",
    }

    def validate(self, memory):
        """
        Validate and normalize a memory.

        Returns:
            (True, normalized_memory)

        Raises:
            ValueError
        """

        if not isinstance(memory, dict):
            raise ValueError(
                "Memory must be a dictionary"
            )

        # ============================================
        # Required fields
        # ============================================

        for field in self.REQUIRED_FIELDS:

            if field not in memory:
                raise ValueError(
                    f"Missing required field: {field}"
                )

            value = memory[field]

            if value is None:
                raise ValueError(
                    f"Field cannot be None: {field}"
                )

            if isinstance(value, str) and not value.strip():
                raise ValueError(
                    f"Field cannot be empty: {field}"
                )

        normalized = dict(memory)

        # ============================================
        # Normalize strings
        # ============================================

        for field in (
            "memory_type",
            "subject",
            "key",
            "value",
        ):
            if isinstance(normalized[field], str):
                normalized[field] = normalized[field].strip()

        # ============================================
        # Memory type
        # ============================================

        memory_type = normalized["memory_type"].lower()

        if memory_type not in self.VALID_MEMORY_TYPES:
            raise ValueError(
                f"Invalid memory_type: {memory_type}"
            )

        normalized["memory_type"] = memory_type

        # ============================================
        # Importance
        # ============================================

        importance = normalized.get(
            "importance",
            0.5,
        )

        try:
            importance = float(importance)
        except (TypeError, ValueError):
            raise ValueError(
                "importance must be a number"
            )

        if not 0.0 <= importance <= 1.0:
            raise ValueError(
                "importance must be between 0 and 1"
            )

        normalized["importance"] = importance

        # ============================================
        # Confidence
        # ============================================

        confidence = normalized.get(
            "confidence",
            0.8,
        )

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            raise ValueError(
                "confidence must be a number"
            )

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        normalized["confidence"] = confidence

        # ============================================
        # List fields
        # ============================================

        for field in self.LIST_FIELDS:

            value = normalized.get(field)

            if value is None:
                normalized[field] = []

            elif not isinstance(value, list):
                raise ValueError(
                    f"{field} must be a list"
                )

        # ============================================
        # Source
        # ============================================

        source = normalized.get(
            "source",
            "conversation",
        )

        if source is None:
            source = "conversation"

        normalized["source"] = str(source).strip()

        # ============================================
        # Decay rate
        # ============================================

        decay_rate = normalized.get(
            "decay_rate",
            0.0,
        )

        try:
            decay_rate = float(decay_rate)
        except (TypeError, ValueError):
            raise ValueError(
                "decay_rate must be a number"
            )

        if decay_rate < 0:
            raise ValueError(
                "decay_rate cannot be negative"
            )

        normalized["decay_rate"] = decay_rate

        # ============================================
        # Expiration
        # ============================================

        if "expires_at" not in normalized:
            normalized["expires_at"] = None

        return True, normalized
