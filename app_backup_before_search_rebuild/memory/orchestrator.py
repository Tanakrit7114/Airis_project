# Phase 5.1 — Memory Orchestrator

from app.memory.query import (
    MemoryQueryResolver,
)

from app.memory.hybrid_retrieval import (
    HybridMemoryRetriever,
)

from app.memory.reranking import (
    MemoryReranker,
)

from app.memory.graph_retrieval import (
    GraphMemoryRetriever,
)


class MemoryOrchestrator:
    """
    Coordinate the complete memory retrieval pipeline.

    Flow:

        Query
          ↓
        Query Resolver
          ↓
        Exact Retrieval
          +
        Hybrid Retrieval
          ↓
        Re-ranking
          ↓
        Graph Expansion
          ↓
        Deduplication
          ↓
        Final Memories
    """

    def __init__(
        self,
        store,
        vector_index=None,
        graph=None,
    ):

        self.store = store

        self.resolver = (
            MemoryQueryResolver()
        )

        self.hybrid = (
            HybridMemoryRetriever(
                store=store,
                vector_index=vector_index,
            )
        )

        self.reranker = (
            MemoryReranker(
                retriever=self.hybrid,
            )
        )

        self.graph_retriever = (
            GraphMemoryRetriever(
                store=store,
                graph=graph,
            )
        )

    # ========================================================
    # Retrieve
    # ========================================================

    def retrieve(
        self,
        query,
        limit=8,
        depth=1,
        min_similarity=0.0,
    ):
        """
        Retrieve the most relevant memories.

        Priority:

            1. Exact resolved memory
            2. Hybrid / reranked memories
            3. Graph expansion

        Results are deduplicated by memory_id.
        """

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        if limit <= 0:
            return []

        # ----------------------------------------------------
        # Query Resolution
        # ----------------------------------------------------

        resolved_key = (
            self.resolver.resolve(query)
        )

        # ----------------------------------------------------
        # Exact memory
        # ----------------------------------------------------

        memories = []

        if resolved_key:

            try:
                exact_memory = (
                    self.store.get_memory_by_key(
                        resolved_key
                    )
                )
            except Exception:
                exact_memory = None

            if exact_memory:

                memories.append(
                    dict(exact_memory)
                )

        # ----------------------------------------------------
        # Seen memory IDs
        # ----------------------------------------------------

        seen = {
            str(item.get("memory_id"))
            for item in memories
            if item.get("memory_id")
            is not None
        }

        # ----------------------------------------------------
        # Hybrid / reranked retrieval
        # ----------------------------------------------------

        try:

            hybrid_results = (
                self.reranker.rerank(
                    query,
                    limit=max(limit, 8),
                    min_similarity=min_similarity,
                )
            )

        except Exception:

            hybrid_results = []

        # ----------------------------------------------------
        # Merge hybrid results
        # ----------------------------------------------------

        for item in hybrid_results:

            memory_id = item.get(
                "memory_id"
            )

            if memory_id is None:
                continue

            memory_id = str(
                memory_id
            )

            if memory_id in seen:
                continue

            seen.add(memory_id)

            memories.append(
                dict(item)
            )

            if len(memories) >= limit:
                break

        # ----------------------------------------------------
        # Direct hybrid fallback
        # ----------------------------------------------------

        if len(memories) < limit:

            try:

                fallback_results = (
                    self.hybrid.rerank(
                        query,
                        limit=max(limit, 8),
                        min_similarity=min_similarity,
                    )
                )

            except Exception:

                fallback_results = []

            for item in fallback_results:

                memory_id = item.get(
                    "memory_id"
                )

                if memory_id is None:
                    continue

                memory_id = str(
                    memory_id
                )

                if memory_id in seen:
                    continue

                seen.add(memory_id)

                memories.append(
                    dict(item)
                )

                if len(memories) >= limit:
                    break

        # ----------------------------------------------------
        # Graph expansion
        # ----------------------------------------------------

        if (
            depth > 0
            and memories
            and len(memories) < limit
        ):

            seed_id = memories[0].get(
                "memory_id"
            )

            if seed_id is not None:

                remaining = (
                    limit
                    - len(memories)
                )

                if remaining > 0:

                    try:

                        graph_results = (
                            self.graph_retriever.retrieve(
                                seed_id,
                                depth=depth,
                                limit=remaining,
                            )
                        )

                    except Exception:

                        graph_results = []

                    for item in graph_results:

                        memory_id = item.get(
                            "memory_id"
                        )

                        if memory_id is None:
                            continue

                        memory_id = str(
                            memory_id
                        )

                        if memory_id in seen:
                            continue

                        seen.add(memory_id)

                        memories.append(
                            dict(item)
                        )

                        if len(memories) >= limit:
                            break

        # ----------------------------------------------------
        # Final deduplication
        # ----------------------------------------------------

        final = []

        final_seen = set()

        for memory in memories:

            memory_id = memory.get(
                "memory_id"
            )

            if memory_id is None:

                # Keep memories without IDs,
                # although normally Memory 2.0
                # memories should always have IDs.
                final.append(memory)
                continue

            memory_id = str(
                memory_id
            )

            if memory_id in final_seen:
                continue

            final_seen.add(
                memory_id
            )

            final.append(memory)

        # ----------------------------------------------------
        # Final limit
        # ----------------------------------------------------

        return final[:limit]