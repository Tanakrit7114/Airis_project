from app.memory.query import MemoryQueryResolver
from app.memory.retrieval import MemoryRetriever
from app.memory.hybrid import HybridMemoryRetriever


def build_context(memory, query, limit=8):
    sections = []

    if not isinstance(query, str):
        return ""

    query = query.strip()

    if not query:
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
        result = memory.get_memory_by_key(resolved_key)

        if result:
            memories.append(result)

    # ========================================================
    # 3. General Memory Retrieval
    # ========================================================

    if not memories:
        retriever = MemoryRetriever(memory)

        memories = retriever.retrieve(
            query,
            limit=limit,
        )

    # ========================================================
    # 4. Hybrid Ranking
    # ========================================================

    if memories:
        hybrid = HybridMemoryRetriever()

        memories = hybrid.retrieve(
            query,
            memories,
            limit=limit,
        )

    # ========================================================
    # 5. Long-Term Memory Context
    # ========================================================

    if memories:
        memory_lines = []

        for item in memories:
            key = item.get("key", "")
            value = item.get("value", "")

            if key and value:
                memory_lines.append(
                    f"- {key}: {value}"
                )

        if memory_lines:
            sections.append(
                "[LONG-TERM MEMORY]\n"
                + "\n".join(memory_lines)
            )

    # ========================================================
    # 6. Recent Conversation
    # ========================================================

    rows = memory.recent(limit=8)

    if rows:
        rows.reverse()

        conversation = "\n".join(
            f"[{role}] {content}"
            for role, content, _ in rows
        )

        sections.append(
            "[RECENT CONVERSATION]\n"
            + conversation
        )

    return "\n\n".join(sections)