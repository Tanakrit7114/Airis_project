# Phase 3.1 — Embedding Tests

from app.memory.embedding import EmbeddingModel


def test_embedding_base_interface():
    model = EmbeddingModel()

    try:
        model.embed("hello")
    except NotImplementedError:
        pass
    else:
        assert False


def test_embed_many_uses_embed():

    class FakeEmbedding(EmbeddingModel):

        def embed(self, text):
            return [float(len(text))]

    model = FakeEmbedding()

    result = model.embed_many([
        "hello",
        "world",
    ])

    assert result == [
        [5.0],
        [5.0],
    ]
