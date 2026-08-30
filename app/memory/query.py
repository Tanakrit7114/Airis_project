import re


class MemoryQueryResolver:

    def resolve(self, query: str):
        q = query.lower().strip()

        # -------------------------
        # Favorite programming language
        # -------------------------

        programming_patterns = [
            r"favorite.*programming.*language",
            r"favourite.*programming.*language",
            r"programming.*language.*like",
            r"programming.*language.*prefer",
            r"preferred.*programming.*language",
            r"programming.*language.*favorite",
        ]

        if any(re.search(pattern, q) for pattern in programming_patterns):
            return "favorite_programming_language"

        # -------------------------
        # Favorite color
        # -------------------------

        color_patterns = [
            r"favorite.*color",
            r"favourite.*color",
            r"color.*like",
            r"color.*prefer",
            r"preferred.*color",
            r"which color.*like",
        ]

        if any(re.search(pattern, q) for pattern in color_patterns):
            return "favorite_color"

        # -------------------------
        # Major
        # -------------------------

        major_patterns = [
            r"what.*my major",
            r"what.*major.*i",
            r"my major",
            r"which major",
            r"what.*study",
        ]

        if any(re.search(pattern, q) for pattern in major_patterns):
            return "major"

        return None
