from fastapi import APIRouter, HTTPException
from app.server.schemas import SessionCreate
from pydantic import BaseModel, Field
from app.server.history_sync import snapshot, merge, SyncConflict

class SyncRequest(BaseModel):
    revision: str = Field(max_length=64)
    chats: list[dict] = Field(max_length=1000)

router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_db():
    from app.server.main import state
    return state.db

@router.get('/sync')
def read_sync():
    with get_db().connect() as con: return snapshot(con)

@router.post('/sync')
def write_sync(payload: SyncRequest):
    try: return merge(get_db(),payload.revision,payload.chats)
    except SyncConflict as exc: raise HTTPException(409,str(exc)) from exc
    except (ValueError,KeyError,TypeError) as exc: raise HTTPException(400,'ประวัติไม่ถูกต้อง: '+str(exc)) from exc


@router.get("/sessions")
def sessions():
    return get_db().list_sessions()


@router.post("/sessions")
def create_session(payload: SessionCreate):
    return get_db().create_session(payload.title)


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    db = get_db()
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"session": session, "messages": db.list_messages(session_id)}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    if not get_db().delete_session(session_id):
        raise HTTPException(404, "Session not found")
    return {"deleted": True}
