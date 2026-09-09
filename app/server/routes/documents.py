from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from app.documents.cloud_fallback import cloud_policy

from app.documents.store import DocumentStore
from app.documents.ocr import process_document

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
    content = await file.read(25*1024*1024+1)
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
    document = get_store().get(document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    return FileResponse(document["storage_path"], filename=document["filename"], media_type=document["mime_type"])


@router.post("/ocr")
async def ocr_document(file: UploadFile = File(...), allow_cloud: bool = Form(False), x_kku_key: str | None = Header(None), x_kku_models: str | None = Header(None)):
    """Backward-compatible OCR endpoint for older clients."""
    try:
        content = await file.read(25*1024*1024+1)
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
