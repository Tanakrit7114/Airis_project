from app.memory.memory_graph import MemoryGraph
from app.memory.graph_traversal import MemoryGraphTraversal


def test_neighbors():
    graph = MemoryGraph()

    graph.add_link("a", "b")

    traversal = MemoryGraphTraversal(graph)

    assert traversal.neighbors("a") == ["b"]


def test_traverse_depth_one():
    graph = MemoryGraph()

    graph.add_link("a", "b")
    graph.add_link("b", "c")

    traversal = MemoryGraphTraversal(graph)

    assert traversal.traverse("a", depth=1) == ["b"]


def test_traverse_depth_two():
    graph = MemoryGraph()

    graph.add_link("a", "b")
    graph.add_link("b", "c")

    traversal = MemoryGraphTraversal(graph)

    assert traversal.traverse("a", depth=2) == ["b", "c"]


def test_traverse_avoids_cycles():
    graph = MemoryGraph()

    graph.add_link("a", "b")
    graph.add_link("b", "c")
    graph.add_link("c", "a")

    traversal = MemoryGraphTraversal(graph)

    result = traversal.traverse("a", depth=5)

    assert result == ["b", "c"]