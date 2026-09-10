"""PDF utilities used by the document routes.

The merge operation intentionally keeps all input data in memory.  The limits
below keep the endpoint bounded while avoiding any user supplied filesystem
paths.  PyMuPDF is imported lazily so the rest of the document API can still
start and report a useful 503 when the optional runtime dependency is missing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from app.documents.ocr import MAX_FILE_BYTES


MIN_MERGE_FILES = 2
MAX_MERGE_FILES = 20
MAX_MERGE_TOTAL_BYTES = 100 * 1024 * 1024
MAX_MERGE_PAGES = 500


class PDFMergeError(ValueError):
    """A client-correctable error while validating or merging PDFs."""


def _display_name(filename: str | None, index: int) -> str:
    """Return a safe, short name for an error message."""

    if filename:
        return Path(filename).name or f"file {index}"
    return f"file {index}"


def _validate_pdf_header(filename: str, content: bytes, index: int) -> None:
    name = _display_name(filename, index)
    if not filename or Path(filename).suffix.lower() != ".pdf":
        raise PDFMergeError(f"ไฟล์ลำดับที่ {index} ({name}) ต้องเป็นไฟล์ PDF (.pdf)")
    # PDF readers may tolerate arbitrary prefixes, but accepting them here
    # makes it too easy to send a renamed non-PDF to the merge endpoint.
    if not content.startswith(b"%PDF-"):
        raise PDFMergeError(f"ไฟล์ลำดับที่ {index} ({name}) ไม่ใช่ PDF ที่ถูกต้อง")


def merge_pdfs(
    files: Sequence[tuple[str | None, bytes]],
    *,
    max_file_bytes: int = MAX_FILE_BYTES,
    max_files: int = MAX_MERGE_FILES,
    max_total_bytes: int = MAX_MERGE_TOTAL_BYTES,
    max_pages: int = MAX_MERGE_PAGES,
) -> bytes:
    """Merge PDFs in the supplied order and return the resulting PDF bytes.

    ``files`` contains ``(filename, content)`` pairs.  Validation happens
    before the output document is created, and every input document is closed
    as soon as its pages have been copied.
    """

    if len(files) < MIN_MERGE_FILES:
        raise PDFMergeError(f"ต้องเลือกไฟล์ PDF อย่างน้อย {MIN_MERGE_FILES} ไฟล์")
    if len(files) > max_files:
        raise PDFMergeError(f"รวม PDF ได้ไม่เกิน {max_files} ไฟล์ต่อครั้ง")
    if max_file_bytes <= 0 or max_total_bytes <= 0 or max_pages <= 0:
        raise ValueError("PDF merge limits must be positive")

    total_bytes = 0
    for index, (filename, content) in enumerate(files, start=1):
        value = content or b""
        name = _display_name(filename, index)
        _validate_pdf_header(filename or "", value, index)
        if len(value) > max_file_bytes:
            raise PDFMergeError(f"ไฟล์ลำดับที่ {index} ({name}) ใหญ่เกิน 25 MB")
        total_bytes += len(value)
        if total_bytes > max_total_bytes:
            limit_mb = max_total_bytes // (1024 * 1024)
            raise PDFMergeError(f"ขนาด PDF รวมเกินขีดจำกัด {limit_mb} MB")

    try:
        import pymupdf
    except ImportError as exc:  # pragma: no cover - depends on installation
        raise RuntimeError("ต้องติดตั้ง PyMuPDF เพื่อรวมไฟล์ PDF") from exc

    merged = pymupdf.open()
    total_pages = 0
    try:
        for index, (filename, content) in enumerate(files, start=1):
            name = _display_name(filename, index)
            source = None
            try:
                source = pymupdf.open(stream=content, filetype="pdf")
                if source.needs_pass:
                    raise PDFMergeError(f"ไฟล์ลำดับที่ {index} ({name}) ติดรหัสผ่าน ไม่สามารถรวมได้")
                page_count = source.page_count
                total_pages += page_count
                if total_pages > max_pages:
                    raise PDFMergeError(f"จำนวนหน้ารวมเกินขีดจำกัด {max_pages} หน้า")
                merged.insert_pdf(source)
            except PDFMergeError:
                raise
            except Exception as exc:
                raise PDFMergeError(f"อ่านไฟล์ลำดับที่ {index} ({name}) ไม่สำเร็จ: PDF อาจเสียหาย") from exc
            finally:
                if source is not None:
                    source.close()

        if total_pages == 0:
            raise PDFMergeError("ไฟล์ PDF ที่เลือกไม่มีหน้าเอกสาร")
        return merged.tobytes()
    finally:
        merged.close()
