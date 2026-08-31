# Phase 5.2 — Memory Context Builder


class MemoryContextBuilder:
    """
    Convert retrieved memories into a compact context
    that can be injected into the Local LLM prompt.

    Flow:

        Retrieved Memories
                ↓
        Deduplicate
                ↓
        Rank / Order
                ↓
        Format
                ↓
        LLM Context
    """

    def __init__(self, max_memories=8):
        self.max_memories = max_memories

    # ========================================================
    # Build
    # ========================================================

    def build(self, memories, limit=None):
        """
        Build formatted memory context.

        Args:
            memories:
                List of memory dictionaries.

            limit:
                Optional maximum number of memories.

        Returns:
            String context.
        """

        if not memories:
            return ""

        if not isinstance(memories, (list, tuple)):
            return ""

        if limit is None:
            limit = self.max_memories

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = self.max_memories

        if limit <= 0:
            return ""

        # ----------------------------------------------------
        # Deduplicate
        # ----------------------------------------------------

        unique = []
        seen = set()

        for memory in memories:

            if not isinstance(memory, dict):
                continue

            memory_id = memory.get("memory_id")

            if memory_id is not None:
                identity = f"id:{memory_id}"
            else:
                identity = (
                    f"key:{memory.get('key', '')}"
                    f"|value:{memory.get('value', '')}"
                )

            if identity in seen:
                continue

            seen.add(identity)
            unique.append(memory)

        if not unique:
            return ""

        # ----------------------------------------------------
        # Sort by relevance
        # ----------------------------------------------------

        unique.sort(
            key=lambda memory: (
                self._safe_float(
                    memory.get(
                        "relevance_score",
                        0.0,
                    )
                ),
                self._safe_float(
                    memory.get(
                        "hybrid_score",
                        0.0,
                    )
                ),
                self._safe_float(
                    memory.get(
                        "importance",
                        0.0,
                    )
                ),
                self._safe_float(
                    memory.get(
                        "confidence",
                        0.0,
                    )
                ),
            ),
            reverse=True,
        )

        unique = unique[:limit]

        # ----------------------------------------------------
        # Format
        # ----------------------------------------------------

        lines = [
            "[MEMORY CONTEXT]"
        ]

        for memory in unique:
            formatted = self._format_memory(memory)

            if formatted:
                lines.append(formatted)

        if len(lines) == 1:
            return ""

        lines.append(
            "[END MEMORY CONTEXT]"
        )

        return "\n".join(lines)

    # ========================================================
    # Format one memory
    # ========================================================

    def _format_memory(self, memory):

        key = str(
            memory.get("key", "")
        ).strip()

        value = str(
            memory.get("value", "")
        ).strip()

        content = str(
            memory.get("content", "")
        ).strip()

        importance = self._safe_float(
            memory.get(
                "importance",
                0.0,
            )
        )

        confidence = self._safe_float(
            memory.get(
                "confidence",
                0.0,
            )
        )

        if content:
            statement = content

        elif key and value:
            statement = f"{key}: {value}"

        elif value:
            statement = value

        elif key:
            statement = key

        else:
            return ""

        return (
            f"- {statement}"
            f" | importance={importance:.2f}"
            f" | confidence={confidence:.2f}"
        )

    # ========================================================
    # Safe float
    # ========================================================

    @staticmethod
    def _safe_float(value):

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return 0.0