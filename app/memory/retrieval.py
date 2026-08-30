# Phase 2.1 — Memory Retrieval
# app/memory/retrieval.py

class MemoryRetriever:
    """
    Retrieve relevant long-term memories from MemoryStore.
    """

    def __init__(self, store):
        self.store = store

    def retrieve(self, query, limit=8):
        """
        Retrieve memories relevant to the query.
        """

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        if limit <= 0:
            return []

        return self.store.retrieve(
            query,
            limit=limit,
        )

    def retrieve_one(self, query):
        """
        Return the most relevant memory,
        or None when nothing is found.
        """

        memories = self.retrieve(
            query,
            limit=1,
        )

        return memories[0] if memories else None


