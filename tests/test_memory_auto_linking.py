from app.memory.store import MemoryStore
from app.memory.memory_graph import MemoryGraph
from app.memory.auto_linker import MemoryAutoLinker


def add_memory(
    store,
    key,
    value,
    importance=0.5,
    confidence=0.8,
):
    return store.add_memory(
        memory_type="preference",
        subject="user",
        key=key,
        value=value,
        importance=importance,
        confidence=confidence,
    )


# ============================================================
# Basic validation
# ============================================================

def test_auto_linker_invalid_memory():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()
    linker = MemoryAutoLinker(store, graph)

    assert linker.link_memory(None) == []


def test_auto_linker_missing_memory():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()
    linker = MemoryAutoLinker(store, graph)

    assert linker.link_memory("does-not-exist") == []


# ============================================================
# Related memories
# ============================================================

def test_auto_linker_finds_related_memory():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    python_id = add_memory(
        store,
        "favorite_language",
        "Python",
    )

    pytorch_id = add_memory(
        store,
        "python_framework",
        "PyTorch",
    )

    linker = MemoryAutoLinker(store, graph)

    links = linker.link_memory(pytorch_id)

    assert isinstance(links, list)


# ============================================================
# Graph creation
# ============================================================

def test_auto_linker_creates_graph_link():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    language_id = add_memory(
        store,
        "favorite_language",
        "Python",
    )

    framework_id = add_memory(
        store,
        "python_framework",
        "PyTorch",
    )

    linker = MemoryAutoLinker(store, graph)

    linker.link_memory(
        framework_id,
        min_similarity=0.0,
    )

    connected = graph.get_connected_ids(
        framework_id
    )

    assert isinstance(connected, list)


# ============================================================
# No self-link
# ============================================================

def test_auto_linker_does_not_self_link():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    memory_id = add_memory(
        store,
        "favorite_language",
        "Python",
    )

    linker = MemoryAutoLinker(store, graph)

    linker.link_memory(
        memory_id,
        min_similarity=0.0,
    )

    connected = graph.get_connected_ids(
        memory_id
    )

    assert str(memory_id) not in {
        str(item)
        for item in connected
    }


# ============================================================
# Limit
# ============================================================

def test_auto_linker_respects_limit():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    target_id = add_memory(
        store,
        "favorite_language",
        "Python",
    )

    for i in range(10):
        add_memory(
            store,
            f"python_preference_{i}",
            f"Python preference {i}",
        )

    linker = MemoryAutoLinker(store, graph)

    links = linker.link_memory(
        target_id,
        limit=3,
        min_similarity=0.0,
    )

    assert len(links) <= 3


# ============================================================
# Deduplication
# ============================================================

def test_auto_linker_deduplicates_links():
    store = MemoryStore(":memory:")
    graph = MemoryGraph()

    first_id = add_memory(
        store,
        "favorite_language",
        "Python",
    )

    second_id = add_memory(
        store,
        "python_framework",
        "PyTorch",
    )

    linker = MemoryAutoLinker(store, graph)

    linker.link_memory(
        second_id,
        min_similarity=0.0,
    )

    linker.link_memory(
        second_id,
        min_similarity=0.0,
    )

    pairs = [
        (
            str(link.source_id),
            str(link.target_id),
            str(link.relation),
        )
        for link in graph.all_links()
    ]

    assert len(pairs) == len(set(pairs))

