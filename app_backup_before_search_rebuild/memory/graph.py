class MemoryGraph:
    """
    Graph for connecting memories.

    Node:
        A memory entity/key/value.

    Edge:
        A relationship between two nodes.
    """

    def __init__(self):
        self.nodes = {}
        self.edges = {}

    # ========================================================
    # Nodes
    # ========================================================

    def add_node(self, node_id, value=None, node_type="memory"):
        self.nodes[node_id] = {
            "id": node_id,
            "value": value,
            "type": node_type,
        }

        self.edges.setdefault(node_id, set())

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    # ========================================================
    # Edges
    # ========================================================

    def add_edge(self, source, target, relation):
        if source not in self.nodes:
            self.add_node(source)

        if target not in self.nodes:
            self.add_node(target)

        self.edges.setdefault(source, set())

        self.edges[source].add(
            (target, relation)
        )

    def get_neighbors(self, node_id):
        neighbors = []

        for target, relation in self.edges.get(
            node_id,
            set(),
        ):
            neighbors.append(
                {
                    "node": self.nodes.get(target),
                    "relation": relation,
                }
            )

        return neighbors

    # ========================================================
    # Path finding
    # ========================================================

    def find_path(self, start, target, max_hops=5):
        if start not in self.nodes:
            return None

        if target not in self.nodes:
            return None

        queue = [
            (start, [])
        ]

        visited = {start}

        while queue:
            current, path = queue.pop(0)

            if current == target:
                return path

            if len(path) >= max_hops:
                continue

            for next_node, relation in self.edges.get(
                current,
                set(),
            ):
                if next_node in visited:
                    continue

                visited.add(next_node)

                new_path = path + [
                    {
                        "from": current,
                        "relation": relation,
                        "to": next_node,
                    }
                ]

                queue.append(
                    (
                        next_node,
                        new_path,
                    )
                )

        return None
