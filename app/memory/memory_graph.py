# Phase 4.2 — Memory Graph

from collections import deque

from app.memory.memory_link import MemoryLink


class MemoryGraph:
    """
    Graph for storing relationships between memories.

    Supports:
    - Nodes
    - Directed edges
    - Neighbor lookup
    - Multi-hop path finding
    """

    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self._links = []

    # ========================================================
    # Nodes
    # ========================================================

    def add_node(
        self,
        node_id,
        value=None,
        node_type="memory",
        **metadata,
    ):
        """
        Add or update a node in the memory graph.
        """

        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "value": value if value is not None else node_id,
                "type": node_type,
                **metadata,
            }
        else:
            if value is not None:
                self.nodes[node_id]["value"] = value

            self.nodes[node_id]["type"] = node_type
            self.nodes[node_id].update(metadata)

        self.edges.setdefault(node_id, [])

        return self.nodes[node_id]

    # ========================================================
    # Edges
    # ========================================================

    def add_link(
        self,
        source_id,
        target_id,
        relation="related_to",
        strength=1.0,
    ):
        """
        Add a directed relationship.
        """

        if source_id not in self.nodes:
            self.add_node(source_id)

        if target_id not in self.nodes:
            self.add_node(target_id)

        link = MemoryLink(
            source_id,
            target_id,
            relation,
            strength,
        )

        self._links.append(link)

        self.edges.setdefault(source_id, [])

        # Avoid duplicate identical edges
        edge_exists = any(
            target == target_id and rel == relation
            for target, rel in self.edges[source_id]
        )

        if not edge_exists:
            self.edges[source_id].append(
                (target_id, relation)
            )

        return link
    
    # ========================================================
    # All Links
    # ========================================================

    def all_links(self):
        """
        Return all memory links in the graph.
        """

        return list(self._links)

    # ========================================================
    # Compatibility
    # ========================================================

    def add_edge(
        self,
        source_id,
        target_id,
        relation="related_to",
        strength=1.0,
    ):
        """
        Alias for add_link().
        """

        return self.add_link(
            source_id,
            target_id,
            relation,
            strength,
        )

    # ========================================================
    # Remove
    # ========================================================

    def remove_link(
        self,
        source_id,
        target_id,
        relation=None,
    ):
        """
        Remove matching links.

        Returns:
            True if at least one link was removed,
            otherwise False.
        """

        before = len(self._links)

        self._links = [
            link
            for link in self._links
            if not (
                link.source_id == source_id
                and link.target_id == target_id
                and (
                    relation is None
                    or link.relation == relation
                )
            )
        ]

        removed = len(self._links) < before

        if source_id in self.edges:
            self.edges[source_id] = [
                (target, rel)
                for target, rel in self.edges[source_id]
                if not (
                    target == target_id
                    and (
                        relation is None
                        or rel == relation
                    )
                )
            ]

        return removed
    
    # ========================================================
    # Clear
    # ========================================================

    def clear(self):
        """
        Remove all nodes and links from the graph.
        """

        self.nodes.clear()
        self.edges.clear()
        self._links.clear()

    # ========================================================
    # Neighbors
    # ========================================================

    def get_neighbors(self, node_id):
        """
        Return neighboring nodes.
        """

        results = []

        for target_id, relation in self.edges.get(
            node_id,
            [],
        ):
            node = self.nodes.get(target_id)

            if node is None:
                continue

            results.append(
                {
                    "relation": relation,
                    "node": node,
                }
            )

        return results
    
    # ========================================================
    # Connected IDs
    # ========================================================

    def get_connected_ids(self, node_id):
        """
        Return directly connected node IDs.

        Includes both:
        - outgoing connections
        - incoming connections

        Preserves discovery order.
        """

        connected = []
        seen = set()

        # Outgoing
        for target_id, _ in self.edges.get(
            node_id,
            [],
        ):
            if target_id not in seen:
                seen.add(target_id)
                connected.append(target_id)

        # Incoming
        for link in self._links:
            if link.target_id == node_id:
                if link.source_id not in seen:
                    seen.add(link.source_id)
                    connected.append(link.source_id)

        return connected
        
    # ========================================================
    # Length
    # ========================================================

    def __len__(self):
        """
        Return number of links in the graph.
        """
        return len(self._links)

    # ========================================================
    # Links From
    # ========================================================

    def get_links_from(self, node_id):
        """
        Return links originating from node_id.
        """
        return [
            link
            for link in self._links
            if link.source_id == node_id
        ]

    # ========================================================
    # Links To
    # ========================================================

    def get_links_to(self, node_id):
        """
        Return links targeting node_id.
        """
        return [
            link
            for link in self._links
            if link.target_id == node_id
        ]

    # ========================================================
    # All Links
    # ========================================================

    def all_links(self):
        """
        Return a copy of all graph links.
        """
        return list(self._links)
        

    # ========================================================
    # Multi-hop path
    # ========================================================

    def find_path(
        self,
        start_id,
        target_id,
        max_hops=10,
    ):
        """
        Find the shortest directed path between nodes.
        """

        if start_id == target_id:
            return []

        queue = deque()

        queue.append(
            (
                start_id,
                [],
            )
        )

        visited = {start_id}

        while queue:

            current, path = queue.popleft()

            if len(path) >= max_hops:
                continue

            for next_id, relation in self.edges.get(
                current,
                [],
            ):

                if next_id in visited:
                    continue

                step = {
                    "from": current,
                    "relation": relation,
                    "to": next_id,
                }

                new_path = path + [step]

                if next_id == target_id:
                    return new_path

                visited.add(next_id)

                queue.append(
                    (
                        next_id,
                        new_path,
                    )
                )

        return []
    