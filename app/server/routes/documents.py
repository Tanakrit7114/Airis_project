from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import Response
from app.documents.cloud_fallback import cloud_policy

from app.documents.pdf import MAX_MERGE_FILES, MAX_MERGE_TOTAL_BYTES, merge_pdfs
from app.documents.store import DocumentStore
from app.documents.ocr import MAX_FILE_BYTES, process_document

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post('/classify-image')
async def classify_upload(file: UploadFile = File(...)):
    from starlette.concurrency import run_in_threadpool
    from app.images.classifier import classify_image
    content = await file.read(10 * 1024 * 1024 + 1)
    try:
        return await run_in_threadpool(classify_image, content)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except (RuntimeError, ImportError) as exc:
        raise HTTPException(503, str(exc)) from exc


def get_store() -> DocumentStore:
    from app.server.main import state
    return state.documents


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), allow_cloud: bool = Form(False)):
    if not file.filename:
        raise HTTPException(400, "Missing filename")
    content = await file.read(MAX_FILE_BYTES+1)
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(400, "ไฟล์ใหญ่เกิน 25 MB")
    try:
        from app.server.main import state
        from app.server.inference import run_serialized
        from app.images.local_vision import release_text_models
        def ingest():
            release_text_models(state)
            with cloud_policy(allow_cloud):
                return get_store().save(file.filename, content)
        result = await run_serialized(state.lock,ingest)
        return result
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"Document indexing failed: {exc}") from exc


@router.post("/merge")
async def merge_documents(files: list[UploadFile] = File(...)):
    """Merge uploaded PDF files in request order and return a download."""

    if len(files) < 2:
        raise HTTPException(400, "ต้องเลือกไฟล์ PDF อย่างน้อย 2 ไฟล์")
    if len(files) > MAX_MERGE_FILES:
        raise HTTPException(400, f"รวม PDF ได้ไม่เกิน {MAX_MERGE_FILES} ไฟล์ต่อครั้ง")

    payloads: list[tuple[str | None, bytes]] = []
    total_bytes = 0
    for index, file in enumerate(files, start=1):
        if not file.filename:
            raise HTTPException(400, f"ไฟล์ลำดับที่ {index} ไม่มีชื่อไฟล์")
        content = await file.read(MAX_FILE_BYTES + 1)
        if len(content) > MAX_FILE_BYTES:
            raise HTTPException(400, f"ไฟล์ลำดับที่ {index} ใหญ่เกิน 25 MB")
        total_bytes += len(content)
        if total_bytes > MAX_MERGE_TOTAL_BYTES:
            limit_mb = MAX_MERGE_TOTAL_BYTES // (1024 * 1024)
            raise HTTPException(400, f"ขนาด PDF รวมเกินขีดจำกัด {limit_mb} MB")
        payloads.append((file.filename, content))

    from starlette.concurrency import run_in_threadpool

    try:
        merged = await run_in_threadpool(merge_pdfs, payloads, max_file_bytes=MAX_FILE_BYTES)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, "รวมไฟล์ PDF ไม่สำเร็จ") from exc

    return Response(
        content=merged,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="merged.pdf"'},
    )


@router.get("")
def list_documents(limit: int = 100):
    return {"documents": get_store().list(limit)}


@router.get("/{document_id}")
def get_document(document_id: str):
    document = get_store().get(document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    # Do not return the whole original binary; return searchable text/metadata only.
    return document


@router.get("/{document_id}/download")
def download_document(document_id: str):
    from fastapi.responses import FileResponse
    from pathlib import Path

    document = get_store().get(document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    # Validate the persisted path before handing it to FileResponse. This
    # keeps downloads working after a normal restart while preventing a
    # damaged/legacy database row from exposing an arbitrary local file.
    storage_root = Path(get_store().storage_dir).resolve()
    target = Path(str(document.get("storage_path", ""))).resolve()
    if storage_root not in target.parents or not target.is_file():
        raise HTTPException(404, "Document file is no longer available")
    return FileResponse(target, filename=document["filename"], media_type=document["mime_type"])


@router.post("/ocr")
async def ocr_document(file: UploadFile = File(...), allow_cloud: bool = Form(False), x_kku_key: str | None = Header(None), x_kku_models: str | None = Header(None)):
    """Backward-compatible OCR endpoint for older clients."""
    try:
        content = await file.read(MAX_FILE_BYTES+1)
        if not file.filename:
            raise ValueError("Missing filename")
        from app.server.main import state
        from app.server.inference import run_serialized
        from app.images.local_vision import release_text_models
        def extract():
            release_text_models(state)
            with cloud_policy(allow_cloud, x_kku_key, x_kku_models.split(',') if x_kku_models else None):
                return process_document(file.filename,content)
        result = await run_serialized(state.lock,extract)
        return result
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"OCR failed: {exc}") from exc
