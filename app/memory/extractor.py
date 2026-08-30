import re


class MemoryExtractor:

    def extract(self, text: str):

        memories = []

        text_lower = text.lower()

        # -------------------------
        # Favorite programming language
        # -------------------------

        match = re.search(
            r"(?:favorite|favourite)\s+programming\s+language\s+(?:is|=)\s+([A-Za-z0-9+#.-]+)",
            text,
            re.IGNORECASE
        )

        if match:

            language = match.group(1).strip(".,!?")

            memories.append({
                "memory_type": "preference",
                "subject": "user",
                "key": "favorite_programming_language",
                "value": language,
                "importance": 0.95,
                "confidence": 0.95,
            })

        # -------------------------
        # Thai version
        # -------------------------

        match = re.search(
            r"(?:ชอบ|โปรด)\s*(?:ภาษาโปรแกรม|ภาษาเขียนโปรแกรม)?\s*([A-Za-z0-9+#.-]+)",
            text,
            re.IGNORECASE
        )

        if "ชอบ" in text_lower or "โปรด" in text_lower:

            if match:

                value = match.group(1)

                memories.append({
                    "memory_type": "preference",
                    "subject": "user",
                    "key": "programming_language",
                    "value": value,
                    "importance": 0.85,
                    "confidence": 0.75,
                })

        # -------------------------
        # Generic "I use..."
        # -------------------------

        match = re.search(
            r"\bI use\s+(.+)",
            text,
            re.IGNORECASE
        )

        if match:

            value = match.group(1).strip(".,!?")

            memories.append({
                "memory_type": "fact",
                "subject": "user",
                "key": "uses",
                "value": value,
                "importance": 0.70,
                "confidence": 0.85,
            })

        return memories
