# Phase 4.4 — Memory Graph Retrieval

from app.memory.memory_graph import MemoryGraph
from app.memory.graph_traversal import MemoryGraphTraversal


class GraphMemoryRetriever:
    """
    Retrieve memories through graph relationships.

    Supports two modes:

    1. Graph-only mode
       GraphMemoryRetriever(graph)

       Returns connected memory IDs.

    2. Store mode
       GraphMemoryRetriever(store=store, graph=graph)

       Returns connected memory objects.
    """

    def __init__(
        self,
        graph=None,
        store=None,
        traversal=None,
    ):
        self.store = store

        self.graph = (
            graph
            if graph is not None
            else MemoryGraph()
        )

        self.traversal = (
            traversal
            if traversal is not None
            else MemoryGraphTraversal(
                self.graph
            )
        )

    # ========================================================
    # Retrieve
    # ========================================================

    def retrieve(
        self,
        memory_id,
        depth=1,
        limit=8,
    ):
        """
        Retrieve memories connected to a seed.

        Without store:
            returns memory IDs.

        With store:
            returns memory objects.
        """

        if memory_id is None:
            return []

        if depth <= 0:
            return []

        if limit <= 0:
            return []

        connected_ids = self.traversal.traverse(
            memory_id,
            depth=depth,
        )

        if not connected_ids:
            return []

        # ----------------------------------------------------
        # Graph-only mode
        # ----------------------------------------------------

        if self.store is None:
            return connected_ids[:limit]

        # ----------------------------------------------------
        # Store mode
        # ----------------------------------------------------

        memories = []

        for connected_id in connected_ids:

            memory = self.store.get_memory(
                connected_id
            )

            if not memory:
                continue

            memories.append(memory)

            if len(memories) >= limit:
                break

        return memories

    # ========================================================
    # Retrieve with seed
    # ========================================================

    def retrieve_with_seed(
        self,
        memory_id,
        depth=1,
        limit=8,
    ):
        """
        Return seed + connected memories.

        In graph-only mode:
            returns IDs.

        In store mode:
            returns memory objects.
        """

        if memory_id is None:
            return []

        if limit <= 0:
            return []

        # ----------------------------------------------------
        # Graph-only mode
        # ----------------------------------------------------

        if self.store is None:

            connected = self.retrieve(
                memory_id,
                depth=depth,
                limit=max(limit - 1, 0),
            )

            return [
                str(memory_id),
                *connected,
            ][:limit]

        # ----------------------------------------------------
        # Store mode
        # ----------------------------------------------------

        memories = []

        seed = self.store.get_memory(
            memory_id
        )

        if seed:
            memories.append(seed)

        remaining = limit - len(memories)

        if remaining <= 0:
            return memories[:limit]

        connected = self.retrieve(
            memory_id,
            depth=depth,
            limit=remaining,
        )

        memories.extend(connected)

        return memories[:limit]
