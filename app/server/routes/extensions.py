from urllib.parse import quote
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from app.server.schemas import ExtensionActionRequest

router = APIRouter(prefix="/api/extensions", tags=["extensions"])


def manager():
    from app.server.main import state
    return state.extensions


@router.get("")
def extensions():
    return manager().list_extensions()


@router.get("/{extension_id}/connect")
def connect(extension_id: str):
    try:
        url = manager().connect_url(extension_id)
    except KeyError:
        raise HTTPException(404, "Extension not found")
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"extension_id": extension_id, "authorize_url": url}


@router.get("/oauth/{provider}/callback")
def callback(provider: str, code: str | None = Query(None), state: str | None = Query(None), error: str | None = Query(None)):
    if error:
        return HTMLResponse(f"<html><body><h2>JARVIS Extension</h2><p>Authorization failed: {quote(error)}</p><script>window.close()</script></body></html>", status_code=400)
    if not code or not state:
        return HTMLResponse("<html><body><h2>JARVIS Extension</h2><p>OAuth callback ขาด code/state</p></body></html>", status_code=400)
    try:
        extension_id = manager().handle_callback(provider, code, state)
    except Exception as exc:
        return HTMLResponse(f"<html><body><h2>JARVIS Extension</h2><p>เชื่อมต่อไม่สำเร็จ: {quote(str(exc))}</p></body></html>", status_code=400)
    base = "<html><body><h2>เชื่อมต่อสำเร็จ</h2><p>JARVIS เชื่อมต่อ Extension เรียบร้อยแล้ว</p><script>window.opener && window.opener.postMessage({type:'jarvis-extension-connected',extension:'" + extension_id + "'}, '*'); window.close();</script></body></html>"
    return HTMLResponse(base)


@router.post("/{extension_id}/disconnect")
def disconnect(extension_id: str):
    manager().disconnect(extension_id)
    return {"ok": True}


@router.get("/{extension_id}/test")
def test(extension_id: str):
    try:
        return manager().test(extension_id)
    except Exception as exc:
        raise HTTPException(400, str(exc))


@router.post("/{extension_id}/action")
def action(extension_id: str, payload: ExtensionActionRequest):
    try:
        return manager().action(extension_id, payload.action, payload.query or "")
    except Exception as exc:
        raise HTTPException(400, str(exc))
