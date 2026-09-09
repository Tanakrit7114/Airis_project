# Phase 5.0 — Memory Query Resolver

import re


class MemoryQueryResolver:
    """
    Resolve natural-language queries into canonical memory keys.

    Example:

        "What programming language do I like?"
            ↓
        "favorite_language"
    """

    def resolve(self, query: str):
        if not isinstance(query, str):
            return None

        q = query.lower().strip()

        if not q:
            return None

        # ====================================================
        # Favorite programming language
        # ====================================================

        programming_patterns = [
            r"favorite.*programming.*language",
            r"favourite.*programming.*language",
            r"programming.*language.*like",
            r"programming.*language.*prefer",
            r"preferred.*programming.*language",
            r"programming.*language.*favorite",
            r"programming.*language.*favourite",
            r"what.*programming.*language",
            r"which.*programming.*language",
            r"what.*language.*program",
            r"which.*language.*program",
        ]

        if any(
            re.search(pattern, q)
            for pattern in programming_patterns
        ):
            return "favorite_language"

        # ====================================================
        # Favorite color
        # ====================================================

        color_patterns = [
            r"favorite.*color",
            r"favourite.*color",
            r"color.*like",
            r"color.*prefer",
            r"preferred.*color",
            r"which.*color.*like",
            r"what.*color.*like",
        ]

        if any(
            re.search(pattern, q)
            for pattern in color_patterns
        ):
            return "favorite_color"

        # ====================================================
        # Major
        # ====================================================

        major_patterns = [
            r"what.*my major",
            r"what.*major.*i",
            r"my major",
            r"which major",
            r"what.*study",
            r"what.*do.*i.*study",
            r"what.*am.*i.*studying",
        ]

        if any(
            re.search(pattern, q)
            for pattern in major_patterns
        ):
            return "major"

        # ====================================================
        # Direct canonical key
        # ====================================================

        canonical_keys = {
            "favorite_language",
            "favorite_color",
            "major",
        }

        if q in canonical_keys:
            return q

        return None