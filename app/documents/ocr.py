from __future__ import annotations

import io
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_PAGES = 50
MAX_TEXT_CHARS = 30_000

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
PDF_EXTENSIONS = {".pdf"}


def _truncate(text: str, max_chars: int | None = MAX_TEXT_CHARS) -> str:
    text = text.strip()
    if max_chars is None or len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[OCR text truncated]"


def _vision_ocr_image(path: Path) -> str:
    if platform.system() != "Darwin":
        raise RuntimeError("Apple Vision OCR is available on macOS only")

    try:
        from Foundation import NSURL
        from Vision import (
            VNImageRequestHandler,
            VNRecognizeTextRequest,
            VNRequestTextRecognitionLevelAccurate,
        )
        from Quartz import CGImageSourceCreateImageAtIndex, CGImageSourceCreateWithURL
    except ImportError as exc:
        raise RuntimeError(
            "Apple Vision OCR is not installed. Run: "
            "pip install pyobjc-framework-Vision pyobjc-framework-Quartz"
        ) from exc

    url = NSURL.fileURLWithPath_(str(path))
    source = CGImageSourceCreateWithURL(url, None)
    if source is None:
        raise RuntimeError(f"Cannot read image: {path.name}")
    image = CGImageSourceCreateImageAtIndex(source, 0, None)
    if image is None:
        raise RuntimeError(f"Cannot decode image: {path.name}")

    request = VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(VNRequestTextRecognitionLevelAccurate)
    request.setAutomaticallyDetectsLanguage_(True)
    request.setUsesLanguageCorrection_(True)

    handler = VNImageRequestHandler.alloc().initWithCGImage_options_(image, {})
    success, error = handler.performRequests_error_([request], None)
    if not success:
        raise RuntimeError(f"Vision OCR failed: {error}")

    lines: list[str] = []
    for observation in request.results() or []:
        candidates = observation.topCandidates_(1)
        if candidates:
            value = str(candidates[0].string()).strip()
            if value:
                lines.append(value)
    return "\n".join(lines)


def _tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def _tesseract_ocr_image(path: Path) -> str:
    if not _tesseract_available():
        raise RuntimeError(
            "No OCR engine available. On macOS, install Apple Vision dependencies "
            "or install Tesseract with Homebrew."
        )
    # Thai + English; if tha data is unavailable, retry English-only.
    for languages in ("tha+eng", "eng"):
        result = subprocess.run(
            ["tesseract", str(path), "stdout", "-l", languages, "--psm", "6"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    raise RuntimeError((result.stderr or "Tesseract OCR failed").strip())


def _local_ocr_image(path: Path) -> tuple[str, str]:
    if os.getenv("AIRIS_OCR_MODE","enhanced")=="enhanced":
        try:
            from app.images.local_vision import describe,VISION_MODEL
            return describe(path.read_bytes()),"ollama:"+VISION_MODEL
        except Exception:
            # Preserve a local, non-generative fallback when the VLM is absent.
            pass
    if platform.system() == "Darwin":
        try:
            return _vision_ocr_image(path), "apple-vision"
        except Exception as vision_error:
            if _tesseract_available():
                return _tesseract_ocr_image(path), "tesseract"
            raise vision_error
    return _tesseract_ocr_image(path), "tesseract"

def _ocr_image(path: Path) -> tuple[str, str]:
    try:
        text, engine = _local_ocr_image(path)
        if text.strip() and text.count('[อ่านไม่ชัด]') < 3:
            return text, engine
    except Exception:
        pass
    from app.documents.cloud_fallback import transcribe
    return transcribe(path.read_bytes())


def _pdf_text_and_ocr(path: Path, max_text_chars: int | None = MAX_TEXT_CHARS) -> tuple[str, int, str, int]:
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required. Run: pip install pymupdf") from exc

    with pymupdf.open(path) as doc:
        if len(doc) > MAX_PAGES:
            raise RuntimeError(f"PDF has {len(doc)} pages; maximum is {MAX_PAGES}")

        chunks: list[str] = []
        ocr_pages = 0
        engine = "native"
        for index, page in enumerate(doc):
            native = page.get_text("text").strip()
            if native:
                chunks.append(f"[Page {index + 1}]\n{native}")
                continue

            # Higher resolution helps small glyphs; cap pixels for giant pages.
            dpi=min(300,72*(24_000_000/max(1,page.rect.width*page.rect.height))**0.5)
            pix = page.get_pixmap(dpi=max(72,int(dpi)), alpha=False)
            image_bytes = pix.tobytes("png")
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(image_bytes)
                tmp_path = Path(tmp.name)
            try:
                text, page_engine = _ocr_image(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)
            if text.strip():
                chunks.append(f"[Page {index + 1}]\n{text.strip()}")
                ocr_pages += 1
                engine = page_engine if engine == "native" else engine

        mode = "native+" + engine if ocr_pages else "native"
        return _truncate("\n\n".join(chunks), max_text_chars), len(doc), mode, ocr_pages


def process_document(filename: str, content: bytes, *, max_text_chars: int | None = MAX_TEXT_CHARS) -> dict[str, Any]:
    suffix = Path(filename).suffix.lower()
    if suffix not in IMAGE_EXTENSIONS | PDF_EXTENSIONS:
        raise ValueError("รองรับเฉพาะ PDF, PNG, JPG, JPEG, WEBP, BMP, TIF และ TIFF")
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("ไฟล์ใหญ่เกิน 25 MB")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        path = Path(tmp.name)

    try:
        if suffix == ".pdf":
            text, pages, engine, ocr_pages = _pdf_text_and_ocr(path, max_text_chars)
        else:
            text, engine = _ocr_image(path)
            text = _truncate(text, max_text_chars)
            pages = 1
            ocr_pages = 1
    finally:
        path.unlink(missing_ok=True)

    return {
        "filename": filename,
        "size_bytes": len(content),
        "pages": pages,
        "ocr_pages": ocr_pages,
        "engine": engine,
        "text": text,
        "characters": len(text),
    }
