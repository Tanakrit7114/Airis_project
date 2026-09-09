from app.memory.memory_graph import MemoryGraph
from app.memory.graph_retrieval import GraphMemoryRetriever


def test_retrieve_connected_memory():
    graph = MemoryGraph()

    graph.add_link("a", "b")

    retriever = GraphMemoryRetriever(graph)

    assert retriever.retrieve("a") == ["b"]


def test_retrieve_multiple_depths():
    graph = MemoryGraph()

    graph.add_link("a", "b")
    graph.add_link("b", "c")

    retriever = GraphMemoryRetriever(graph)

    assert retriever.retrieve("a", depth=2) == ["b", "c"]


def test_retrieve_respects_limit():
    graph = MemoryGraph()

    graph.add_link("a", "b")
    graph.add_link("a", "c")
    graph.add_link("a", "d")

    retriever = GraphMemoryRetriever(graph)

    result = retriever.retrieve(
        "a",
        depth=1,
        limit=2,
    )

    assert result == ["b", "c"]


def test_retrieve_avoids_cycles():
    graph = MemoryGraph()

    graph.add_link("a", "b")
    graph.add_link("b", "c")
    graph.add_link("c", "a")

    retriever = GraphMemoryRetriever(graph)

    result = retriever.retrieve(
        "a",
        depth=5,
    )

    assert result == ["b", "c"]
