from pathlib import Path

from app.documents.store import DocumentStore


def test_document_store_persists_and_searches(tmp_path: Path):
    db = tmp_path / "jarvis.db"
    files = tmp_path / "files"
    store = DocumentStore(str(db), str(files))
    result = store.save("lecture.md", "Machine Learning\nPerceptron และ ADALINE".encode())
    assert result["searchable"] is True
    assert (files / f"{result['sha256']}.md").exists()
    loaded = store.get(result["id"])
    assert loaded and "Perceptron" in loaded["text"]
    hits = store.search("Perceptron", limit=5)
    assert hits and hits[0]["document_id"] == result["id"]


def test_duplicate_upload_is_not_stored_twice(tmp_path: Path):
    db = tmp_path / "jarvis.db"
    store = DocumentStore(str(db), str(tmp_path / "files"))
    first = store.save("a.txt", b"hello world")
    second = store.save("copy.txt", b"hello world")
    assert second["id"] == first["id"]
    assert second["reused"] is True
    assert len(store.list()) == 1
