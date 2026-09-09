# Phase 3.4 — Memory Vector Index

from app.memory.vector_index import MemoryVectorIndex


class FakeEmbeddingModel:

    def embed(self, text):
        if not text:
            return []

        return [1.0, 0.0, 0.0]


def make_memory(
    memory_id="memory_1",
    key="favorite_language",
    value="Python",
):
    return {
        "memory_id": memory_id,
        "memory_type": "preference",
        "subject": "user",
        "key": key,
        "value": value,
        "content": f"{key}: {value}",
    }


def test_index_starts_empty():

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    assert len(index) == 0


def test_index_memory():

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    memory = make_memory()

    result = index.index_memory(memory)

    assert result is True
    assert len(index) == 1


def test_index_memory_vector_exists():

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    memory = make_memory()

    index.index_memory(memory)

    vector = index.get_vector(
        "memory_1"
    )

    assert vector == [
        1.0,
        0.0,
        0.0,
    ]


def test_index_many():

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    memories = [
        make_memory(
            memory_id="memory_1"
        ),
        make_memory(
            memory_id="memory_2",
            key="favorite_food",
            value="Italian",
        ),
    ]

    result = index.index_memories(
        memories
    )

    assert result == 2
    assert len(index) == 2


def test_search():

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    index.index_memory(
        make_memory()
    )

    result = index.search(
        "programming language"
    )

    assert len(result) == 1
    assert result[0]["memory_id"] == "memory_1"


def test_remove_memory():

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    index.index_memory(
        make_memory()
    )

    result = index.remove_memory(
        "memory_1"
    )

    assert result is True
    assert len(index) == 0


def test_empty_query():

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    assert index.search("") == []


def test_invalid_memory():

    index = MemoryVectorIndex(
        embedding_model=FakeEmbeddingModel()
    )

    assert index.index_memory(None) is False
