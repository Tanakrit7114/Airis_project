import pytest
from app.documents.ocr import process_document


def test_ocr_rejects_unsupported_extension():
    with pytest.raises(ValueError):
        process_document("notes.docx", b"abc")


def test_ocr_rejects_oversized_file():
    with pytest.raises(ValueError):
        process_document("notes.png", b"x" * (25 * 1024 * 1024 + 1))
