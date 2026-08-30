from app.memory.relationship import RelationshipTracker


def make_memory(**overrides):
    memory = {
        "memory_id": "memory-1",
        "memory_type": "project",
        "subject": "JARVIS",
        "key": "project",
        "value": "Local AI",
        "relationships": [],
    }

    memory.update(overrides)

    return memory


def make_relationship(
    relationship_type="uses",
    source="memory-1",
    target="memory-2",
):
    return {
        "type": relationship_type,
        "source": source,
        "target": target,
    }


def test_add_relationship():
    tracker = RelationshipTracker()

    memory = make_memory()

    result = tracker.add_relationship(
        memory,
        make_relationship(),
    )

    assert len(result["relationships"]) == 1
    assert result["relationships"][0]["type"] == "uses"


def test_add_relationship_normalizes_values():
    tracker = RelationshipTracker()

    memory = make_memory()

    relationship = {
        "type": " uses ",
        "source": " memory-1 ",
        "target": " memory-2 ",
    }

    result = tracker.add_relationship(
        memory,
        relationship,
    )

    assert result["relationships"][0] == {
        "type": "uses",
        "source": "memory-1",
        "target": "memory-2",
    }


def test_duplicate_relationship_is_not_added():
    tracker = RelationshipTracker()

    memory = make_memory()

    relationship = make_relationship()

    memory = tracker.add_relationship(
        memory,
        relationship,
    )

    memory = tracker.add_relationship(
        memory,
        relationship,
    )

    assert len(memory["relationships"]) == 1


def test_get_relationships():
    tracker = RelationshipTracker()

    memory = make_memory(
        relationships=[
            make_relationship(),
            make_relationship(
                relationship_type="related_to",
                source="memory-1",
                target="memory-3",
            ),
        ]
    )

    relationships = tracker.get_relationships(
        memory
    )

    assert len(relationships) == 2
    assert relationships[0]["type"] == "uses"
    assert relationships[1]["type"] == "related_to"


def test_remove_relationship():
    tracker = RelationshipTracker()

    memory = make_memory()

    relationship = make_relationship()

    memory = tracker.add_relationship(
        memory,
        relationship,
    )

    memory = tracker.remove_relationship(
        memory,
        relationship,
    )

    assert memory["relationships"] == []


def test_has_relationship():
    tracker = RelationshipTracker()

    memory = make_memory()

    relationship = make_relationship()

    memory = tracker.add_relationship(
        memory,
        relationship,
    )

    assert tracker.has_relationship(
        memory,
        relationship,
    )


def test_invalid_relationship_is_ignored():
    tracker = RelationshipTracker()

    memory = make_memory()

    result = tracker.add_relationship(
        memory,
        {
            "type": "",
            "source": "",
            "target": "",
        },
    )

    assert result["relationships"] == []


def test_invalid_memory():
    tracker = RelationshipTracker()

    assert tracker.add_relationship(
        None,
        make_relationship(),
    ) is None

    assert tracker.get_relationships(
        None
    ) == []


def test_find_related_memories():
    tracker = RelationshipTracker()

    memory_1 = make_memory(
        memory_id="memory-1"
    )

    memory_1 = tracker.add_relationship(
        memory_1,
        make_relationship(
            source="memory-1",
            target="memory-2",
        ),
    )

    memory_2 = make_memory(
        memory_id="memory-2"
    )

    memory_3 = make_memory(
        memory_id="memory-3"
    )

    related = tracker.find_related_memories(
        memory_1,
        [
            memory_2,
            memory_3,
        ],
    )

    assert len(related) == 1
    assert related[0]["memory_id"] == "memory-2"
