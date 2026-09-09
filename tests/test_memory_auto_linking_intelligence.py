from app.memory.store import MemoryStore
from app.memory.memory_graph import MemoryGraph
from app.memory.auto_linker import MemoryAutoLinker


def add_memory(
    store,
    key,
    value,
    memory_type="preference",
    subject="user",
    importance=0.5,
    confidence=0.8,
    tags=None,
    entities=None,
):
    return store.add_memory(
        memory_type=memory_type,
        subject=subject,
        key=key,
        value=value,
        importance=importance,
        confidence=confidence,
        tags=tags or [],
        entities=entities or [],
    )


# ============================================================
# Strong relationship should be linked
# ============================================================

def test_auto_link_strongly_related_memories():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    first_id = add_memory(
        store,
        "favorite_language",
        "Python",
        tags=["programming", "ai"],
        entities=["Python", "AI"],
        importance=1.0,
        confidence=1.0,
    )

    second_id = add_memory(
        store,
        "python_framework",
        "PyTorch",
        tags=["programming", "ai"],
        entities=["Python", "AI", "PyTorch"],
        importance=1.0,
        confidence=1.0,
    )

    linker = MemoryAutoLinker(
        store=store,
        graph=graph,
    )

    links = linker.auto_link(
        first_id,
        limit=5,
    )

    assert links
    assert any(
        str(link.target_id) == str(second_id)
        for link in links
    )


# ============================================================
# Weak relationship should not be linked
# ============================================================

def test_auto_link_rejects_unrelated_memory():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    first_id = add_memory(
        store,
        "favorite_language",
        "Python",
        tags=["programming"],
        entities=["Python"],
    )

    second_id = add_memory(
        store,
        "favorite_food",
        "Pizza",
        memory_type="fact",
        subject="world",
        tags=["food"],
        entities=["Pizza"],
    )

    linker = MemoryAutoLinker(
        store=store,
        graph=graph,
    )

    links = linker.auto_link(
        first_id,
        limit=5,
    )

    assert not any(
        str(link.target_id) == str(second_id)
        for link in links
    )


# ============================================================
# Relationship strength should be stored in graph
# ============================================================

def test_auto_link_stores_relationship_strength():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    first_id = add_memory(
        store,
        "python_interest",
        "Python",
        tags=["programming", "ai"],
        entities=["Python", "AI"],
    )

    second_id = add_memory(
        store,
        "pytorch_interest",
        "PyTorch",
        tags=["programming", "ai"],
        entities=["Python", "AI", "PyTorch"],
    )

    linker = MemoryAutoLinker(
        store=store,
        graph=graph,
    )

    links = linker.auto_link(
        first_id,
        limit=5,
    )

    assert links

    link = links[0]

    assert hasattr(link, "strength")
    assert 0.0 <= float(link.strength) <= 1.0


# ============================================================
# Duplicate links should not be created
# ============================================================

def test_auto_link_does_not_duplicate_links():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    first_id = add_memory(
        store,
        "python_interest",
        "Python",
        tags=["programming", "ai"],
        entities=["Python", "AI"],
    )

    second_id = add_memory(
        store,
        "pytorch_interest",
        "PyTorch",
        tags=["programming", "ai"],
        entities=["Python", "AI", "PyTorch"],
    )

    linker = MemoryAutoLinker(
        store=store,
        graph=graph,
    )

    linker.auto_link(
        first_id,
        limit=5,
    )

    linker.auto_link(
        first_id,
        limit=5,
    )

    matching_links = [
        link
        for link in graph.all_links()
        if (
            str(link.source_id) == str(first_id)
            and str(link.target_id) == str(second_id)
        )
    ]

    assert len(matching_links) == 1


# ============================================================
# Limit should be respected
# ============================================================

def test_auto_link_respects_limit():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    first_id = add_memory(
        store,
        "python",
        "Python",
        tags=["programming", "ai"],
        entities=["Python", "AI"],
    )

    for i in range(10):
        add_memory(
            store,
            f"python_project_{i}",
            "Python AI project",
            tags=["programming", "ai"],
            entities=["Python", "AI"],
        )

    linker = MemoryAutoLinker(
        store=store,
        graph=graph,
    )

    links = linker.auto_link(
        first_id,
        limit=3,
    )

    assert len(links) <= 3

