from fastapi import APIRouter, HTTPException
import asyncio, os, platform, requests
from pathlib import Path
from app.server.inference import run_serialized
from app.server.schemas import ModelSelectRequest

router = APIRouter(prefix="/api/models", tags=["models"])

OLLAMA_MODELS = [
    ("qwen2.5-coder:7b", "4.7 GB", "coding / fast"),
    ("qwen2.5-coder:14b", "9.0 GB", "coding / balanced"),
    ("qwen3:14b", "9.3 GB", "general / balanced"),
    ("devstral-small-2:latest", "15 GB", "agentic coding"),
    ("qwen3-coder:30b", "18 GB", "coding / high quality"),
    ("qwen3.6:27b", "17 GB", "general / high quality"),
    ("qwen3.6:35b-a3b-q4_K_M", "23 GB", "general / highest quality"),
]

def state():
    from app.server.main import state
    return state

def catalog():
    st=state(); sys=platform.system(); machine=platform.machine().lower()
    items=[]
    if sys=="Darwin" and machine in {"arm64","aarch64"}:
        for model,size,desc in [("mlx-community/Qwen3-8B-4bit","~5 GB","fast/default"),("mlx-community/Qwen3-14B-4bit","~9 GB","higher quality")]:
            cache=Path(os.getenv("HF_HOME", str(Path.home()/".cache/huggingface")))/"hub"/("models--"+model.replace("/","--"))/"snapshots"
            installed=cache.is_dir() and any(cache.iterdir())
            items.append({"id":model,"name":model.split('/')[-1],"backend":"mlx","installed":installed,"size":size,"speed_hint":"fast" if "8B" in model else "balanced","description":desc})
    else:
        root=Path("models")
        for path in sorted(root.glob("*.gguf")) if root.exists() else []:
            items.append({"id":str(path),"name":path.name,"backend":"llama.cpp","installed":True,"size":f"{path.stat().st_size/1024**3:.1f} GB","speed_hint":"depends on GPU/CPU","description":"Local GGUF model"})
        if not items:
            items.append({"id":st.assistant.llm.config.model,"name":st.assistant.llm.config.model,"backend":"llama.cpp","installed":Path(st.assistant.llm.config.model).is_file(),"size":"unknown","speed_hint":"depends on hardware","description":"Set MODEL/LLAMA_MODEL_PATH to a GGUF file"})
    # Keep these choices visible even when Ollama is temporarily stopped; the
    # backend reports a clear error/fallback instead of leaving the UI blank.
    installed_names=set()
    try:
        response=requests.get("http://127.0.0.1:11434/api/tags",timeout=2)
        response.raise_for_status()
        installed_names={m["name"] for m in response.json().get("models",[])}
    except (requests.RequestException, ValueError, KeyError):
        pass
    for model, size, desc in OLLAMA_MODELS:
        items.append({"id": model, "name": model, "backend": "ollama", "installed": model in installed_names,
                      "size": size, "speed_hint": desc.split(" / ")[-1], "description": desc})
    return items

@router.get("")
def models():
    st=state(); return {"current": {"model":st.assistant.llm.config.model,"backend":st.assistant.llm.model_manager.backend_name,"status":st.assistant.llm.model_manager.status}, "rag": {"model":st.assistant.rag_llm.config.model,"backend":st.assistant.rag_llm.model_manager.backend_name,"status":st.assistant.rag_llm.model_manager.status}, "platform":{"system":platform.system(),"machine":platform.machine()}, "models":catalog()}

@router.post("/select")
async def select(payload: ModelSelectRequest):
    st=state(); choices={x["id"] for x in await asyncio.to_thread(catalog)}
    if payload.model not in choices:
        raise HTTPException(400, "Model is not in the supported catalog")
    try:
        await run_serialized(st.lock, st.assistant.llm.model_manager.switch_model, payload.model, payload.backend)
        return {"ok":True,"model":st.assistant.llm.config.model,"backend":st.assistant.llm.model_manager.backend_name,"status":st.assistant.llm.model_manager.status}
    except Exception as exc:
        raise HTTPException(400,str(exc)) from exc

@router.post("/rag/select")
async def select_rag(payload: ModelSelectRequest):
    st=state(); choices={x["id"] for x in await asyncio.to_thread(catalog)}
    if payload.model not in choices:
        raise HTTPException(400, "Model is not in the supported catalog")
    try:
        # Keep the RAG choice lightweight until retrieval actually needs it.
        await run_serialized(st.lock, st.assistant.rag_llm.model_manager.switch_model, payload.model, payload.backend, False)
        return {"ok":True,"model":st.assistant.rag_llm.config.model,"backend":st.assistant.rag_llm.model_manager.backend_name,"status":st.assistant.rag_llm.model_manager.status}
    except Exception as exc:
        raise HTTPException(400,str(exc)) from exc
