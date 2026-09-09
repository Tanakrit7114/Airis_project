import importlib
import platform


def test_llm_module_imports_without_eager_mlx(monkeypatch):
    real_system = platform.system
    real_machine = platform.machine
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    mod = importlib.import_module("app.llm")
    assert hasattr(mod, "ModelManager")


def test_memory_vector_index_uses_platform_fallback(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    from app.memory.platform_embedding import create_embedding_model, HashEmbeddingModel
    model = create_embedding_model()
    assert isinstance(model, HashEmbeddingModel)
    assert len(model.embed("hello university")) == 384
