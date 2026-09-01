from app.memory.store import MemoryStore
from app.memory.memory_graph import MemoryGraph
from app.memory.auto_linker import MemoryAutoLinker


def add_memory(
    store,
    key,
    value,
    memory_type="preference",
    importance=0.5,
    confidence=0.8,
    tags=None,
    entities=None,
):
    return store.add_memory(
        memory_type=memory_type,
        subject="user",
        key=key,
        value=value,
        importance=importance,
        confidence=confidence,
        tags=tags,
        entities=entities,
    )


# ============================================================
# Relationship type
# ============================================================

def test_relationship_has_type():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    language_id = add_memory(
        store,
        "favorite_language",
        "Python",
        tags=["programming"],
        entities=["Python"],
    )

    framework_id = add_memory(
        store,
        "python_framework",
        "PyTorch",
        tags=["programming", "machine-learning"],
        entities=["Python", "PyTorch"],
    )

    linker = MemoryAutoLinker(
        store=store,
        graph=graph,
    )

    links = linker.link_memory(
        framework_id,
        min_similarity=0.0,
    )

    assert isinstance(links, list)

    if links:
        assert hasattr(links[0], "relation")
        assert links[0].relation


# ============================================================
# Relationship strength
# ============================================================

def test_relationship_has_strength():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    language_id = add_memory(
        store,
        "favorite_language",
        "Python",
        tags=["programming"],
        entities=["Python"],
    )

    framework_id = add_memory(
        store,
        "python_framework",
        "PyTorch",
        tags=["programming"],
        entities=["Python", "PyTorch"],
    )

    linker = MemoryAutoLinker(
        store=store,
        graph=graph,
    )

    links = linker.link_memory(
        framework_id,
        min_similarity=0.0,
    )

    for link in links:
        assert isinstance(
            link.strength,
            (int, float),
        )
        assert 0.0 <= link.strength <= 1.0


# ============================================================
# Entity-based relationship
# ============================================================

def test_entity_overlap_can_create_relationship():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    python_id = add_memory(
        store,
        "favorite_language",
        "Python",
        entities=["Python"],
    )

    pytorch_id = add_memory(
        store,
        "framework",
        "PyTorch",
        entities=["Python", "PyTorch"],
    )

    linker = MemoryAutoLinker(
        store=store,
        graph=graph,
    )

    linker.link_memory(
        pytorch_id,
        min_similarity=0.0,
    )

    connected = graph.get_connected_ids(
        pytorch_id
    )

    assert str(python_id) in {
        str(item)
        for item in connected
    }


# ============================================================
# Tag-based relationship
# ============================================================

def test_tag_overlap_can_create_relationship():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    first_id = add_memory(
        store,
        "python_interest",
        "Python",
        tags=[
            "programming",
            "machine-learning",
        ],
    )

    second_id = add_memory(
        store,
        "pytorch_interest",
        "PyTorch",
        tags=[
            "programming",
            "machine-learning",
        ],
    )

    linker = MemoryAutoLinker(
        store=store,
        graph=graph,
    )

    linker.link_memory(
        second_id,
        min_similarity=0.0,
    )

    connected = graph.get_connected_ids(
        second_id
    )

    assert str(first_id) in {
        str(item)
        for item in connected
    }


# ============================================================
# Stronger semantic relationship
# ============================================================

def test_shared_entity_relationship_is_strong():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    first_id = add_memory(
        store,
        "favorite_language",
        "Python",
        entities=["Python"],
    )

    second_id = add_memory(
        store,
        "python_framework",
        "PyTorch",
        entities=["Python", "PyTorch"],
    )

    linker = MemoryAutoLinker(
        store=store,
        graph=graph,
    )

    links = linker.link_memory(
        second_id,
        min_similarity=0.0,
    )

    matching = [
        link
        for link in links
        if str(link.target_id)
        == str(first_id)
        or str(link.source_id)
        == str(first_id)
    ]

    assert matching

    assert any(
        link.strength > 0.0
        for link in matching
    )


# ============================================================
# Duplicate relationship protection
# ============================================================

def test_semantic_linking_does_not_duplicate_relationship():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    first_id = add_memory(
        store,
        "favorite_language",
        "Python",
        entities=["Python"],
    )

    second_id = add_memory(
        store,
        "python_framework",
        "PyTorch",
        entities=["Python", "PyTorch"],
    )

    linker = MemoryAutoLinker(
        store=store,
        graph=graph,
    )

    linker.link_memory(
        second_id,
        min_similarity=0.0,
    )

    before = len(graph.all_links())

    linker.link_memory(
        second_id,
        min_similarity=0.0,
    )

    after = len(graph.all_links())

    assert after == before
