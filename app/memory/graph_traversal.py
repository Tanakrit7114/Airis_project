# Phase 4.3 — Memory Graph Traversal

from app.memory.memory_graph import MemoryGraph


class MemoryGraphTraversal:
    """
    Traverse connected memories in a MemoryGraph.
    """

    def __init__(self, graph=None):
        self.graph = graph or MemoryGraph()

    def neighbors(self, memory_id):
        """
        Return directly connected memory IDs.
        """
        if memory_id is None:
            return []

        return self.graph.get_connected_ids(memory_id)

    def traverse(self, memory_id, depth=1):
        """
        Traverse the memory graph from a starting memory.

        Returns memory IDs ordered by discovery.
        """

        if memory_id is None:
            return []

        if depth <= 0:
            return []

        start_id = str(memory_id)

        visited = {start_id}
        frontier = [start_id]
        result = []

        for _ in range(depth):
            next_frontier = []

            for current_id in frontier:
                neighbors = self.graph.get_connected_ids(
                    current_id
                )

                for neighbor_id in neighbors:
                    neighbor_id = str(neighbor_id)

                    if neighbor_id in visited:
                        continue

                    visited.add(neighbor_id)
                    result.append(neighbor_id)
                    next_frontier.append(neighbor_id)

            if not next_frontier:
                break

            frontier = next_frontier

        return result