from app.memory.memory_link import MemoryLink


def test_memory_link_creates_relationship():
    link = MemoryLink(
        "1",
        "2",
        "related_to",
        0.8,
    )

    assert link.source_id == "1"
    assert link.target_id == "2"
    assert link.relation == "related_to"
    assert link.strength == 0.8


def test_memory_link_converts_ids_to_string():
    link = MemoryLink(
        123,
        456,
    )

    assert link.source_id == "123"
    assert link.target_id == "456"


def test_memory_link_clamps_strength():
    low = MemoryLink(
        "1",
        "2",
        strength=-1,
    )

    high = MemoryLink(
        "1",
        "2",
        strength=5,
    )

    assert low.strength == 0.0
    assert high.strength == 1.0


def test_memory_link_to_dict():
    link = MemoryLink(
        "1",
        "2",
        "supports",
        0.9,
    )

    assert link.to_dict() == {
        "source_id": "1",
        "target_id": "2",
        "relation": "supports",
        "strength": 0.9,
    }