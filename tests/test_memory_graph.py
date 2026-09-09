from app.memory.memory_graph import MemoryGraph


def test_add_link():
    graph = MemoryGraph()

    link = graph.add_link(
        "1",
        "2",
        "related_to",
        0.8,
    )

    assert link.source_id == "1"
    assert link.target_id == "2"
    assert link.relation == "related_to"
    assert link.strength == 0.8
    assert len(graph) == 1


def test_get_links_from():
    graph = MemoryGraph()

    graph.add_link(
        "1",
        "2",
        "related_to",
    )

    graph.add_link(
        "1",
        "3",
        "supports",
    )

    links = graph.get_links_from("1")

    assert len(links) == 2
    assert links[0].target_id == "2"
    assert links[1].target_id == "3"


def test_get_links_to():
    graph = MemoryGraph()

    graph.add_link(
        "1",
        "3",
        "related_to",
    )

    graph.add_link(
        "2",
        "3",
        "supports",
    )

    links = graph.get_links_to("3")

    assert len(links) == 2


def test_get_connected_ids():
    graph = MemoryGraph()

    graph.add_link(
        "1",
        "2",
    )

    graph.add_link(
        "1",
        "3",
    )

    graph.add_link(
        "4",
        "1",
    )

    connected = graph.get_connected_ids("1")

    assert set(connected) == {
        "2",
        "3",
        "4",
    }


def test_remove_link():
    graph = MemoryGraph()

    graph.add_link(
        "1",
        "2",
        "related_to",
    )

    assert len(graph) == 1

    removed = graph.remove_link(
        "1",
        "2",
        "related_to",
    )

    assert removed is True
    assert len(graph) == 0


def test_remove_missing_link():
    graph = MemoryGraph()

    removed = graph.remove_link(
        "1",
        "2",
    )

    assert removed is False


def test_all_links_returns_copy():
    graph = MemoryGraph()

    graph.add_link(
        "1",
        "2",
    )

    links = graph.all_links()

    assert len(links) == 1

    links.clear()

    assert len(graph) == 1


def test_clear():
    graph = MemoryGraph()

    graph.add_link("1", "2")
    graph.add_link("2", "3")

    assert len(graph) == 2

    graph.clear()

    assert len(graph) == 0
