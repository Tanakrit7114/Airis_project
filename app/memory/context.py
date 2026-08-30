def build_context(memory, query):
    # Starter version: recent conversation.
    # Semantic memory, embeddings, importance and linking will be added later.
    rows = memory.recent(limit=8)

    if not rows:
        return ""

    rows.reverse()
    return "\n".join(
        f"[{role}] {content}"
        for role, content, _ in rows
    )
