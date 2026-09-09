from fastapi import APIRouter, HTTPException
from app.server.memory_admin import MemoryAdmin
from app.server.inference import run_serialized

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
memory_admin = MemoryAdmin()


def get_state():
    from app.server.main import state
    return state


@router.get("/system")
async def system(benchmark: bool = False):
    state = get_state()
    payload = {
        "model": state.assistant.llm.config.model,
        "model_loaded": state.assistant.llm.model_manager.model is not None,
        "max_generation_tokens": state.assistant.llm.config.max_tokens,
        "websocket_clients": state.active_connections,
        "backend": state.assistant.llm.model_manager.backend_name,
        "llm_status": state.assistant.llm.model_manager.status,
        "platform": __import__("platform").platform(),
    }
    if benchmark:
        payload["benchmark"] = await run_serialized(state.lock, state.assistant.benchmark)
    return payload


@router.get("/memory")
def memories(query: str | None = None, status: str | None = None, limit: int = 100):
    return {"items": memory_admin.list(query, status, max(1, min(limit, 500)))}


@router.patch("/memory/{memory_id}")
def update_memory(memory_id: str, payload: dict):
    updated = memory_admin.update(memory_id, **payload)
    if updated is None:
        raise HTTPException(404, "Memory not found")
    return updated


@router.delete("/memory/{memory_id}")
def delete_memory(memory_id: str):
    if not memory_admin.soft_delete(memory_id):
        raise HTTPException(404, "Memory not found")
    return {"deleted": True}


@router.get("/memory/graph")
def memory_graph():
    return memory_admin.graph()


@router.get("/search-logs")
def search_logs(limit: int = 100):
    return {"items": get_state().db.events("search", min(max(limit, 1), 500))}


@router.get("/tool-logs")
def tool_logs(limit: int = 100):
    return {"items": get_state().db.events("tool", min(max(limit, 1), 500))}


@router.get("/audit-logs")
def audit_logs(limit: int = 100):
    return {"items": get_state().db.events("audit", min(max(limit, 1), 500))}


@router.get("/analytics")
def analytics():
    return get_state().db.analytics()


@router.get("/documents")
def documents(limit: int = 100):
    return {"items": get_state().documents.list(limit)}
