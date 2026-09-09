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
        tags=tags,
        entities=entities,
    )


# ============================================================
# Relationship scoring
# ============================================================

def test_relationship_score_exists():
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

    score = linker.relationship_score(
        first_id,
        second_id,
    )

    assert isinstance(score, (int, float))
    assert 0.0 <= score <= 1.0


# ============================================================
# Shared entity
# ============================================================

def test_shared_entity_increases_relationship_score():
    store = MemoryStore(":memory:")

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

    third_id = add_memory(
        store,
        "favorite_food",
        "Pizza",
        entities=["Pizza"],
    )

    linker = MemoryAutoLinker(store)

    related_score = linker.relationship_score(
        first_id,
        second_id,
    )

    unrelated_score = linker.relationship_score(
        first_id,
        third_id,
    )

    assert related_score > unrelated_score


# ============================================================
# Shared tags
# ============================================================

def test_shared_tags_increase_relationship_score():
    store = MemoryStore(":memory:")

    first_id = add_memory(
        store,
        "python_interest",
        "Python",
        tags=["programming", "ai"],
    )

    second_id = add_memory(
        store,
        "pytorch_interest",
        "PyTorch",
        tags=["programming", "ai"],
    )

    third_id = add_memory(
        store,
        "music_interest",
        "Guitar",
        tags=["music"],
    )

    linker = MemoryAutoLinker(store)

    related_score = linker.relationship_score(
        first_id,
        second_id,
    )

    unrelated_score = linker.relationship_score(
        first_id,
        third_id,
    )

    assert related_score > unrelated_score


# ============================================================
# Same type / subject
# ============================================================

def test_same_memory_type_and_subject_increase_score():
    store = MemoryStore(":memory:")

    first_id = add_memory(
        store,
        "favorite_language",
        "Python",
        memory_type="preference",
        subject="user",
    )

    second_id = add_memory(
        store,
        "favorite_framework",
        "PyTorch",
        memory_type="preference",
        subject="user",
    )

    third_id = add_memory(
        store,
        "random_fact",
        "Earth",
        memory_type="fact",
        subject="world",
    )

    linker = MemoryAutoLinker(store)

    related_score = linker.relationship_score(
        first_id,
        second_id,
    )

    unrelated_score = linker.relationship_score(
        first_id,
        third_id,
    )

    assert related_score > unrelated_score


# ============================================================
# Strong relationship
# ============================================================

def test_strong_relationship_can_be_detected():
    store = MemoryStore(":memory:")

    first_id = add_memory(
        store,
        "favorite_language",
        "Python",
        importance=1.0,
        confidence=1.0,
        tags=["programming", "ai"],
        entities=["Python", "AI"],
    )

    second_id = add_memory(
        store,
        "python_framework",
        "PyTorch",
        importance=1.0,
        confidence=1.0,
        tags=["programming", "ai"],
        entities=["Python", "AI", "PyTorch"],
    )

    linker = MemoryAutoLinker(store)

    score = linker.relationship_score(
        first_id,
        second_id,
    )

    assert score >= 0.5


# ============================================================
# Weak / unrelated relationship
# ============================================================

def test_unrelated_memories_have_low_score():
    store = MemoryStore(":memory:")

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

    linker = MemoryAutoLinker(store)

    score = linker.relationship_score(
        first_id,
        second_id,
    )

    assert 0.0 <= score < 0.5
