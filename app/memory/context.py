from app.memory.query import MemoryQueryResolver
from app.memory.ranking import MemoryRanker
from app.memory.hybrid_retrieval import HybridMemoryRetriever


def build_context(memory, query, limit=8):
    """
    Build context from long-term memory and recent conversation.

    Retrieval strategy:

        1. Resolve known semantic queries to memory keys.
        2. Retrieve exact memory when possible.
        3. Otherwise retrieve candidate memories.
        4. Rank using relevance + importance + confidence + decay.
        5. Prevent clearly irrelevant memories from entering context.
        6. Always preserve useful recent conversation.
    """

    sections = []

    # ========================================================
    # Input validation
    # ========================================================

    if not isinstance(query, str):
        return ""

    query = query.strip()

    if not query:
        return ""

    if not isinstance(limit, int) or limit <= 0:
        return ""

    # ========================================================
    # 1. Query Resolution
    # ========================================================

    resolver = MemoryQueryResolver()
    resolved_key = resolver.resolve(query)

    # ========================================================
    # 2. Exact Memory Retrieval
    # ========================================================

    memories = []

    if resolved_key:
        result = memory.get_memory_by_key(
            resolved_key
        )

        if result:
            memories.append(result)

    # ========================================================
    # 3. Hybrid Memory Retrieval
    # ========================================================

    if not memories:
        retriever = HybridMemoryRetriever(
            store=memory
        )

        try:
            memories = retriever.rerank(
                query,
                limit=max(limit, 8),
            )
        except (TypeError, AttributeError):
            memories = []

    # ========================================================
    # 4. Fallback Memory Retrieval
    # ========================================================
    #
    # The hybrid retriever requires a populated vector index.
    # A newly created retriever may not have the store's vectors.
    #
    # When semantic retrieval returns nothing, inspect active
    # memories directly and rank them using MemoryRanker.
    #

    if not memories:
        try:
            active_memories = memory.active_memories()
        except AttributeError:
            active_memories = []

        if active_memories:
            memories = list(active_memories)

    # ========================================================
    # 5. Relevance + Quality Ranking
    # ========================================================

    if memories:
        ranker = MemoryRanker()
        ranked = []

        query_lower = query.lower()

        # ----------------------------------------------------
        # Detect semantic intent
        # ----------------------------------------------------

        programming_query = (
            "programming language" in query_lower
            or "programming" in query_lower
            or "coding language" in query_lower
            or "code language" in query_lower
        )

        for item in memories:

            if not isinstance(item, dict):
                continue

            relevance = float(
                ranker._relevance(
                    query,
                    item,
                )
            )

            importance = float(
                ranker._importance(item)
            )

            confidence = float(
                ranker._confidence(item)
            )

            decay = float(
                ranker._decay(item)
            )

            key = str(
                item.get("key", "")
            ).lower()

            value = str(
                item.get("value", "")
            ).lower()

            # ------------------------------------------------
            # Semantic relationship
            # ------------------------------------------------

            semantic_hint = False

            # Programming-language memories
            if programming_query:

                programming_memory = (
                    "language" in key
                    or "programming" in key
                    or "coding" in key
                    or key == "important_preference"
                )

                programming_value = (
                    value in {
                        "python",
                        "java",
                        "javascript",
                        "typescript",
                        "c",
                        "c++",
                        "c#",
                        "go",
                        "rust",
                        "ruby",
                        "php",
                        "swift",
                        "kotlin",
                    }
                )

                if (
                    programming_memory
                    or programming_value
                ):
                    semantic_hint = True

            # ------------------------------------------------
            # Direct keyword matching
            # ------------------------------------------------

            searchable = " ".join(
                [
                    key,
                    value,
                    str(
                        item.get(
                            "content",
                            "",
                        )
                    ).lower(),
                ]
            )

            query_words = set(
                query_lower.split()
            )

            searchable_words = set(
                searchable.split()
            )

            overlap = (
                query_words
                & searchable_words
            )

            if overlap:
                semantic_hint = True

            # ------------------------------------------------
            # Exact key match
            # ------------------------------------------------

            exact_key = (
                query_lower == key
            )

            if exact_key:
                semantic_hint = True
                relevance = max(
                    relevance,
                    1.0,
                )

            # ------------------------------------------------
            # Filter irrelevant memories
            # ------------------------------------------------

            if (
                relevance <= 0
                and not semantic_hint
            ):
                continue

            # ------------------------------------------------
            # Ranking score
            # ------------------------------------------------

            ranking_score = (
                relevance * 5.0
                + importance * 2.0
                + confidence * 1.5
                - decay * 5.0
            )

            if semantic_hint:
                ranking_score += 3.0

            # Strongly prefer highly important memories
            # when relevance is similar.
            ranking_score += (
                importance * 1.0
            )

            result = dict(item)

            result["ranking_score"] = (
                ranking_score
            )

            result["_relevance"] = (
                relevance
            )

            result["_semantic_hint"] = (
                semantic_hint
            )

            ranked.append(result)

        # ----------------------------------------------------
        # Sort
        # ----------------------------------------------------

        ranked.sort(
            key=lambda item: (
                item["ranking_score"],
                item.get(
                    "importance",
                    0.0,
                ),
                item.get(
                    "confidence",
                    0.0,
                ),
            ),
            reverse=True,
        )

        memories = ranked[:limit]

    # ========================================================
    # 6. Long-Term Memory Context
    # ========================================================

    if memories:

        memory_lines = []

        for item in memories:

            key = item.get(
                "key",
                "",
            )

            value = item.get(
                "value",
                "",
            )

            if key and value:
                memory_lines.append(
                    f"- {key}: {value}"
                )

        if memory_lines:
            sections.append(
                "[LONG-TERM MEMORY]\n"
                + "\n".join(
                    memory_lines
                )
            )

    # ========================================================
    # 7. Recent Conversation
    # ========================================================

    try:
        rows = memory.recent(
            limit=8
        )
    except AttributeError:
        rows = []

    if rows:

        rows = list(rows)
        rows.reverse()

        conversation_lines = []

        for row in rows:

            if len(row) >= 2:
                role = row[0]
                content = row[1]

                conversation_lines.append(
                    f"[{role}] {content}"
                )

        if conversation_lines:
            sections.append(
                "[RECENT CONVERSATION]\n"
                + "\n".join(
                    conversation_lines
                )
            )

    # ========================================================
    # 8. Final Context
    # ========================================================

    return "\n\n".join(sections)