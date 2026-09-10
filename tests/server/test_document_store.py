from pathlib import Path
import pytest

from app.documents.store import DocumentStore


def _pdf_bytes(*labels: str) -> bytes:
    import pymupdf

    document = pymupdf.open()
    try:
        for label in labels:
            page = document.new_page()
            page.insert_text((72, 72), label)
        return document.tobytes()
    finally:
        document.close()


def test_document_store_persists_and_searches(tmp_path: Path):
    db = tmp_path / "jarvis.db"
    files = tmp_path / "files"
    store = DocumentStore(str(db), str(files))
    result = store.save("lecture.md", "Machine Learning\nPerceptron และ ADALINE".encode())
    assert result["searchable"] is True
    assert (files / f"{result['sha256']}.md").exists()
    loaded = store.get(result["id"])
    assert loaded and "Perceptron" in loaded["text"]
    download_url = f"/api/documents/{result['id']}/download"
    assert result["download_url"] == loaded["download_url"] == store.list()[0]["download_url"] == download_url
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


def test_document_download_returns_original_bytes_and_handles_missing_file(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.server.routes import documents

    store = DocumentStore(str(tmp_path / "db.sqlite"), str(tmp_path / "files"))
    original = b"Airis download verification"
    saved = store.save("report.txt", original)
    monkeypatch.setattr(documents, "get_store", lambda: store)
    app = FastAPI()
    app.include_router(documents.router)
    with TestClient(app) as client:
        response = client.get(saved["download_url"])
        assert response.status_code == 200
        assert response.content == original
        assert "attachment" in response.headers["content-disposition"]
        Path(store.get(saved["id"])["storage_path"]).unlink()
        assert client.get(saved["download_url"]).status_code == 404


def test_document_download_rejects_persisted_path_outside_storage(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.server.routes import documents

    store = DocumentStore(str(tmp_path / "db.sqlite"), str(tmp_path / "files"))
    saved = store.save("report.txt", b"public document")
    outside = tmp_path / "private.txt"
    outside.write_bytes(b"must not be downloaded")
    with store.connect() as con:
        con.execute("UPDATE documents SET storage_path = ? WHERE id = ?", (str(outside), saved["id"]))
        con.commit()
    monkeypatch.setattr(documents, "get_store", lambda: store)
    app = FastAPI()
    app.include_router(documents.router)
    with TestClient(app) as client:
        response = client.get(saved["download_url"])
        assert response.status_code == 404
        assert b"must not be downloaded" not in response.content


@pytest.mark.parametrize("filename", ["large.txt", "large.docx", "large.zip"])
def test_oversized_upload_is_rejected_before_extracting_or_storing(tmp_path, monkeypatch, filename):
    from app.documents import store as store_module
    monkeypatch.setattr(store_module, "MAX_FILE_BYTES", 8)
    monkeypatch.setattr(store_module, "_extract_text", lambda *args: pytest.fail("Must reject before extraction"))
    files = tmp_path / "files"
    store = DocumentStore(str(tmp_path / "jarvis.db"), str(files))
    with pytest.raises(ValueError, match="25 MB"):
        store.save(filename, b"x" * 9)
    assert store.list() == []
    assert list(files.iterdir()) == []


def test_upload_endpoint_rejects_oversize_before_model_unload(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.server.routes import documents
    monkeypatch.setattr(documents, "MAX_FILE_BYTES", 8)
    monkeypatch.setattr(documents, "get_store", lambda: pytest.fail("Oversized input must not be indexed"))
    app = FastAPI()
    app.include_router(documents.router)
    with TestClient(app) as client:
        response = client.post("/api/documents/upload", files={"file": ("large.txt", b"x" * 100)})
    assert response.status_code == 400
    assert "25 MB" in response.json()["detail"]


def test_merge_endpoint_preserves_pdf_order():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    import pymupdf
    from app.server.routes import documents

    first = _pdf_bytes("first page")
    second = _pdf_bytes("second page", "third page")
    app = FastAPI()
    app.include_router(documents.router)

    with TestClient(app) as client:
        response = client.post(
            "/api/documents/merge",
            files=[
                ("files", ("one.pdf", first, "application/pdf")),
                ("files", ("two.pdf", second, "application/pdf")),
            ],
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    merged = pymupdf.open(stream=response.content, filetype="pdf")
    try:
        assert merged.page_count == 3
        assert [page.get_text().strip() for page in merged] == [
            "first page",
            "second page",
            "third page",
        ]
    finally:
        merged.close()


@pytest.mark.parametrize(
    ("files", "message"),
    [
        ([('files', ('one.txt', b'%PDF-1.7', 'application/pdf')), ('files', ('two.pdf', _pdf_bytes('ok'), 'application/pdf'))], "PDF"),
        ([('files', ('one.pdf', b'not a pdf', 'application/pdf')), ('files', ('two.pdf', _pdf_bytes('ok'), 'application/pdf'))], "ไม่ใช่ PDF"),
    ],
)
def test_merge_endpoint_rejects_non_pdf_inputs(files, message):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.server.routes import documents

    app = FastAPI()
    app.include_router(documents.router)
    with TestClient(app) as client:
        response = client.post("/api/documents/merge", files=files)

    assert response.status_code == 400
    assert message in response.json()["detail"]


def test_merge_endpoint_rejects_too_few_files():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.server.routes import documents

    app = FastAPI()
    app.include_router(documents.router)
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/merge",
            files={"files": ("one.pdf", _pdf_bytes("only"), "application/pdf")},
        )

    assert response.status_code == 400
    assert "อย่างน้อย 2" in response.json()["detail"]


def test_merge_endpoint_rejects_oversized_input_before_merge(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.server.routes import documents

    monkeypatch.setattr(documents, "MAX_FILE_BYTES", 8)
    app = FastAPI()
    app.include_router(documents.router)
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/merge",
            files=[
                ("files", ("one.pdf", b"%PDF-" + b"x" * 20, "application/pdf")),
                ("files", ("two.pdf", b"%PDF-" + b"y" * 20, "application/pdf")),
            ],
        )

    assert response.status_code == 400
    assert "25 MB" in response.json()["detail"]
