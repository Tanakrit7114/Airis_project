# Phase 1.1 — Memory 2.0
# app/memory/extractor.py

import re


class MemoryExtractor:
    """
    Extract structured memories from natural language.

    Deterministic rule-based extractor.
    Predictable, testable, and easy to extend.
    """

    # ============================================================
    # Preference
    # ============================================================

    PREFERENCE_PATTERNS = [
        # My favorite programming language is Python
        # My favorite color is purple
        (
            re.compile(
                r"\bmy\s+favorite\s+"
                r"(?P<category>programming\s+language|color)\s+"
                r"is\s+"
                r"(?P<value>[^.!?]+)",
                re.IGNORECASE,
            ),
            "favorite",
        ),

        # I like blue
        # I like Italian food
        # I love Python
        # I prefer Rust
        (
            re.compile(
                r"\b(?:i\s+)?(?:really\s+)?"
                r"(?:like|love|prefer)\s+"
                r"(?P<value>[^.!?]+)",
                re.IGNORECASE,
            ),
            "preference",
        ),
    ]

    # ============================================================
    # Profile
    # ============================================================

    PROFILE_PATTERNS = [
        (
            re.compile(
                r"\bmy\s+name\s+is\s+(?P<value>[^.!?]+)",
                re.IGNORECASE,
            ),
            "name",
        ),
        (
            re.compile(
                r"\bi\s+am\s+(?!working\s+on\b)"
                r"(?P<value>[^.!?]+)",
                re.IGNORECASE,
            ),
            "identity",
        ),
    ]

    # ============================================================
    # Project
    # ============================================================

    PROJECT_PATTERNS = [
        (
            re.compile(
                r"\b(?:i\s+am\s+)?working\s+on\s+"
                r"(?P<value>[^.!?]+)",
                re.IGNORECASE,
            ),
            "current_project",
        ),
        (
            re.compile(
                r"\bmy\s+project\s+is\s+"
                r"(?P<value>[^.!?]+)",
                re.IGNORECASE,
            ),
            "current_project",
        ),
    ]

    # ============================================================
    # Tasks / Goals
    # ============================================================

    TASK_PATTERNS = [
        (
            re.compile(
                r"\b(?:i\s+)?need\s+to\s+"
                r"(?P<value>[^.!?]+)",
                re.IGNORECASE,
            ),
            "task",
        ),
        (
            re.compile(
                r"\b(?:i\s+)?want\s+to\s+"
                r"(?P<value>[^.!?]+)",
                re.IGNORECASE,
            ),
            "goal",
        ),
    ]

    # ============================================================
    # Helpers
    # ============================================================

    def _clean(self, value):
        """
        Normalize extracted values.

        Examples:
            "Python." -> "Python"
            "Italian   food." -> "Italian food"
            "  Python  programming  " -> "Python programming"
        """

        if value is None:
            return ""

        value = str(value).strip()

        # Normalize all whitespace, including repeated spaces/tabs/newlines.
        value = re.sub(r"\s+", " ", value)

        # Remove sentence punctuation from the edges only.
        value = value.strip(" \t\r\n.,;:!?")

        return value

    # ============================================================
    # Memory creation
    # ============================================================

    def _make_memory(
        self,
        memory_type,
        key,
        value,
        source="conversation",
        importance=0.5,
        confidence=0.8,
    ):
        value = self._clean(value)

        if not value:
            return None

        return {
            "memory_type": memory_type,
            "subject": "user",
            "key": key,
            "value": value,
            "importance": importance,
            "confidence": confidence,
            "source": source,
        }

    # ============================================================
    # Preference key inference
    # ============================================================

    def _preference_key(self, value):
        """
        Infer a useful preference key from the value.

        Examples:
            Python       -> favorite_programming_language
            Rust         -> favorite_programming_language
            purple       -> favorite_color
            blue         -> favorite_color
            Italian food -> preference
        """

        normalized = self._clean(value).lower()

        language_names = {
            "python",
            "rust",
            "javascript",
            "typescript",
            "java",
            "c",
            "c++",
            "c#",
            "go",
            "golang",
            "swift",
            "kotlin",
            "php",
            "ruby",
            "dart",
        }

        if normalized in language_names:
            return "favorite_language"

        color_names = {
            "red",
            "orange",
            "yellow",
            "green",
            "blue",
            "purple",
            "pink",
            "black",
            "white",
            "gray",
            "grey",
            "brown",
            "cyan",
            "magenta",
        }

        if normalized in color_names:
            return "favorite_color"

        return "preference"

    # ============================================================
    # Pattern extraction
    # ============================================================

    def _extract_patterns(self, text, patterns):
        memories = []

        if patterns is self.PREFERENCE_PATTERNS:
            memory_type = "preference"
        elif patterns is self.PROFILE_PATTERNS:
            memory_type = "profile"
        elif patterns is self.PROJECT_PATTERNS:
            memory_type = "project"
        else:
            memory_type = "task"

        for pattern, key in patterns:
            match = pattern.search(text)

            if not match:
                continue

            value = self._clean(match.group("value"))

            if not value:
                continue

            importance = 0.5
            confidence = 0.8
            final_key = key

            # ====================================================
            # Preference
            # ====================================================

            if memory_type == "preference":
                if key == "favorite":
                    category = match.groupdict().get("category")

                    if category:
                        category = self._clean(category).lower()

                        if category == "programming language":
                            final_key = "favorite_programming_language"

                        elif category == "color":
                            final_key = "favorite_color"

                        importance = 0.95
                        confidence = 0.98

                    else:
                        final_key = self._preference_key(value)

                        importance = 0.9
                        confidence = 0.9

                else:
                    final_key = self._preference_key(value)

                    importance = 0.85
                    confidence = 0.9

            # ====================================================
            # Profile
            # ====================================================

            elif memory_type == "profile":
                importance = 0.95
                confidence = 0.95

            # ====================================================
            # Project
            # ====================================================

            elif memory_type == "project":
                importance = 0.85
                confidence = 0.9

            # ====================================================
            # Task / Goal
            # ====================================================

            elif memory_type == "task":
                if key == "goal":
                    importance = 0.8
                    confidence = 0.9
                else:
                    importance = 0.85
                    confidence = 0.9

            memory = self._make_memory(
                memory_type=memory_type,
                key=final_key,
                value=value,
                importance=importance,
                confidence=confidence,
            )

            if memory:
                memories.append(memory)

        return memories

    # ============================================================
    # Main extraction
    # ============================================================

    def extract(self, text):
        """
        Extract all memories from text.

        Returns:
            list[dict]
        """

        # None / non-string / empty input must safely return [].
        if text is None:
            return []

        if not isinstance(text, str):
            text = str(text)

        text = self._clean(text)

        if not text:
            return []

        memories = []

        # --------------------------------------------------------
        # Preference
        # --------------------------------------------------------

        memories.extend(
            self._extract_patterns(
                text,
                self.PREFERENCE_PATTERNS,
            )
        )

        # --------------------------------------------------------
        # Profile
        # --------------------------------------------------------

        memories.extend(
            self._extract_patterns(
                text,
                self.PROFILE_PATTERNS,
            )
        )

        # --------------------------------------------------------
        # Project
        # --------------------------------------------------------

        memories.extend(
            self._extract_patterns(
                text,
                self.PROJECT_PATTERNS,
            )
        )

        # --------------------------------------------------------
        # Tasks / Goals
        # --------------------------------------------------------

        memories.extend(
            self._extract_patterns(
                text,
                self.TASK_PATTERNS,
            )
        )

        return memories

    # ============================================================
    # Extract one
    # ============================================================

    def extract_one(self, text):
        """
        Return the first extracted memory.

        Returns:
            dict | None
        """

        memories = self.extract(text)

        if not memories:
            return None

        return memories[0]