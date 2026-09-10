from fastapi import APIRouter, HTTPException
import asyncio, copy, hashlib, math, os, platform, requests, threading, time
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

_KKU_CACHE={"signature":"","expires":0.0,"models":[]}
_KKU_LOCK=threading.Lock()
_KKU_ICONS={"Claude":"◈","Deepseek":"◉","Gemini":"✦","Meta AI":"∞","MiniMax":"▥","Mistral":"△","MoonshotAI":"◐","Nova (AWS)":"◆","OpenAI":"◎","Qwen":"◇","xAI":"𝕏"}

# KKU's model catalogue is OpenAI-compatible, but it does not consistently
# publish quota/context metadata for every model. Keep the values returned by
# KKU when present and label Airis' own request ceiling separately so the UI
# never presents an estimate as an account quota.
KKU_ENDPOINT = "https://gen.ai.kku.ac.th/api/v1"
KKU_AIRIS_OUTPUT_LIMIT = 4096
KKU_DIRECT_CONTEXT_LIMIT = 100_000
_TOKEN_FIELDS = (
    "context_window", "context_length", "context_length_tokens", "max_context_tokens",
    "max_input_tokens", "input_token_limit", "token_limit",
)
_OUTPUT_FIELDS = ("max_output_tokens", "output_token_limit", "max_completion_tokens")


def _raw_number(raw, fields):
    if not isinstance(raw, dict):
        return None
    for field in fields:
        value = raw.get(field)
        if isinstance(value, bool):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            continue
        if math.isfinite(number) and number > 0 and number.is_integer():
            return int(number)
    return None


def _kku_capabilities(model: str, raw=None):
    """Return capabilities Airis can actually route to this model.

    Web search and website generation are Airis tools/prompts, so they are
    available to every text model. Image generation is a separate local FLUX
    service and is intentionally marked as such rather than attributed to KKU.
    """
    return {
        "chat": True,
        # This route sends text messages only; provider/model naming cannot
        # establish that Airis can pass image inputs to the selected model.
        "vision": False,
        "vision_note": "Airis KKU chat sends text only; document images use the separate OCR service",
        "web_search": True,
        "website_generation": True,
        "image_generation": False,
        "image_generation_via": "Airis local FLUX",
    }


def _kku_limits(raw=None):
    context = _raw_number(raw, _TOKEN_FIELDS)
    output = _raw_number(raw, _OUTPUT_FIELDS)
    return {
        "context_window": context,
        "max_output_tokens": output,
        "airis_output_tokens": KKU_AIRIS_OUTPUT_LIMIT,
        "airis_context_chars": KKU_DIRECT_CONTEXT_LIMIT,
        "reported_by_kku": bool(context or output),
        "usage_available": False,
    }


def _kku_item(model, *, name=None, description="KKU", provider="KKU", installed=True, raw=None):
    return {
        "id": model, "name": name or model, "backend": "kku", "installed": installed,
        "size": "cloud", "speed_hint": "cloud", "description": description,
        "icon": _KKU_ICONS.get(provider, "☁"), "provider": provider,
        "limits": _kku_limits(raw), "observed": None,
        "capabilities": _kku_capabilities(model, raw),
    }


def _with_observations(items):
    from app.server.kku_fallback import observed_model_usage
    observed = observed_model_usage()
    result = copy.deepcopy(items)
    for item in result:
        if item.get("backend") != "kku":
            continue
        current = observed.get(item.get("id"))
        item["observed"] = current
        item["limits"] = {
            **(item.get("limits") or {}),
            "usage_available": bool(current and current.get("model_quota")),
        }
    return result


def kku_catalog():
    """Discover the user's current KKU model catalog with a bounded stale cache."""
    key=os.getenv("KKU_API_KEY","").strip()
    configured=[m.strip() for m in os.getenv("KKU_CHAT_MODELS","gemini-3.5-flash-lite").split(",") if m.strip()]
    if not key:
        return _with_observations([
            _kku_item(m, description="KKU Generative AI API · API key required", installed=False)
            for m in dict.fromkeys(configured)
        ])
    signature=hashlib.sha256(key.encode()).hexdigest()[:12]
    now=time.monotonic()
    with _KKU_LOCK:
        if _KKU_CACHE["signature"]==signature and _KKU_CACHE["models"] and now<_KKU_CACHE["expires"]:
            return _with_observations(_KKU_CACHE["models"])
        stale=_KKU_CACHE["models"] if _KKU_CACHE["signature"]==signature else []
        try:
            response=requests.get("https://gen.ai.kku.ac.th/api/v1/models",headers={"Authorization":"Bearer "+key,"Accept":"application/json"},timeout=(5,20),allow_redirects=False)
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data", []) if isinstance(payload, dict) else []
            discovered=[];seen=set()
            for raw in data[:200] if isinstance(data,list) else []:
                if not isinstance(raw,dict):continue
                if not isinstance(raw.get("id"), str): continue
                model=raw["id"].strip();owner=str(raw.get("owned_by","KKU")).strip()[:80] or "KKU"
                if not model or len(model)>200 or model in seen:continue
                seen.add(model);name=str(raw.get("display_name") or model).strip()[:200]
                discovered.append(_kku_item(model, name=name, description="KKU · "+owner, provider=owner,
                                            raw=raw))
            if not discovered:raise ValueError("KKU returned an empty model catalog")
            _KKU_CACHE.update(signature=signature,expires=now+300,models=discovered)
            return _with_observations(discovered)
        except (requests.RequestException,ValueError,TypeError):
            if stale:return _with_observations(stale)
            return _with_observations([_kku_item(m, description="KKU configured fallback") for m in dict.fromkeys(configured)])

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
    installed_models={}
    try:
        response=requests.get("http://127.0.0.1:11434/api/tags",timeout=2)
        response.raise_for_status()
        for item in response.json().get("models",[]):
            if isinstance(item,dict) and isinstance(item.get("name"),str) and item["name"].strip():
                installed_models[item["name"]]=item
    except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError):
        pass
    for model, size, desc in OLLAMA_MODELS:
        items.append({"id": model, "name": model, "backend": "ollama", "installed": model in installed_models,
                      "size": size, "speed_hint": desc.split(" / ")[-1], "description": desc})
    recommended={model for model,_,_ in OLLAMA_MODELS}
    for model,details in sorted(installed_models.items()):
        if model in recommended: continue
        size=details.get("size")
        items.append({"id":model,"name":model,"backend":"ollama","installed":True,
                      "size":f"{size/1024**3:.1f} GB" if isinstance(size,(int,float)) else "local",
                      "speed_hint":"depends on hardware","description":"Installed in Ollama"})
    items.extend(kku_catalog())
    return items

@router.get("")
def models():
    st=state(); current={"model":st.kku_model,"backend":"kku","status":"ready"} if st.chat_provider=="kku" else {"model":st.assistant.llm.config.model,"backend":st.assistant.llm.model_manager.backend_name,"status":st.assistant.llm.model_manager.status}
    available_models = catalog()
    try:
        from app.server.kku_fallback import observed_model_usage
        observed = observed_model_usage()
    except (ImportError, AttributeError):
        observed = {}
    latest_observation = max((float(item.get("last_seen", 0)) for item in observed.values()), default=0)
    quota_observed = any(bool(item.get("model_quota")) for item in observed.values())
    for item in available_models:
        if item.get("backend") == "kku":
            current_observation = observed.get(item.get("id"))
            item["observed"] = current_observation
            item["limits"] = {
                **(item.get("limits") or {}),
                "usage_available": bool(current_observation and current_observation.get("model_quota")),
            }
    return {
        "current": current,
        "rag": {"model":st.assistant.rag_llm.config.model,"backend":st.assistant.rag_llm.model_manager.backend_name,"status":st.assistant.rag_llm.model_manager.status},
        "platform":{"system":platform.system(),"machine":platform.machine()},
        "kku": {
            "configured": bool(os.getenv("KKU_API_KEY", "").strip()),
            "endpoint": KKU_ENDPOINT,
            "catalog_endpoint": KKU_ENDPOINT + "/models",
            "usage_available": quota_observed,
            "usage_note": (
                "แสดงจาก model_quota ใน response ล่าสุดของ KKU"
                if quota_observed
                else "KKU API ไม่ส่งโควตาการใช้งานคงเหลือผ่าน endpoint /models; จะปรากฏหลังเรียกใช้งานจริง"
            ),
            "observed_models": len(observed),
            "observed_updated_at": latest_observation or None,
            "airis_output_tokens": KKU_AIRIS_OUTPUT_LIMIT,
            "airis_context_chars": KKU_DIRECT_CONTEXT_LIMIT,
        },
        "models":available_models,
    }

@router.post("/select")
async def select(payload: ModelSelectRequest):
    st=state(); selected=_resolve_model(payload,await asyncio.to_thread(catalog))
    if selected["backend"]=="kku":
        if not os.getenv("KKU_API_KEY", "").strip():
            raise HTTPException(400,"KKU_API_KEY is not configured")
        st.chat_provider="kku";st.kku_model=payload.model
        return {"ok":True,"model":payload.model,"backend":"kku","status":"ready"}
    try:
        await run_serialized(st.lock, st.assistant.llm.model_manager.switch_model, payload.model, selected["backend"])
        st.chat_provider="local";st.kku_model=None
        return {"ok":True,"model":st.assistant.llm.config.model,"backend":st.assistant.llm.model_manager.backend_name,"status":st.assistant.llm.model_manager.status}
    except Exception as exc:
        raise HTTPException(400,str(exc)) from exc

@router.post("/rag/select")
async def select_rag(payload: ModelSelectRequest):
    st=state(); selected=_resolve_model(payload,await asyncio.to_thread(catalog))
    if selected["backend"]=="kku":
        raise HTTPException(400,"RAG requires a local model; select KKU as the chat model instead")
    try:
        # Keep the RAG choice lightweight until retrieval actually needs it.
        await run_serialized(st.lock, st.assistant.rag_llm.model_manager.switch_model, payload.model, selected["backend"], False)
        return {"ok":True,"model":st.assistant.rag_llm.config.model,"backend":st.assistant.rag_llm.model_manager.backend_name,"status":st.assistant.rag_llm.model_manager.status}
    except Exception as exc:
        raise HTTPException(400,str(exc)) from exc


def _resolve_model(payload: ModelSelectRequest, choices: list[dict]) -> dict:
    matches=[item for item in choices if item["id"]==payload.model]
    if payload.backend and payload.backend!="auto":
        matches=[item for item in matches if item["backend"]==payload.backend]
    if not matches:
        raise HTTPException(400,"Model and backend are not in the supported catalog")
    if len({item["backend"] for item in matches})>1:
        raise HTTPException(400,"Choose a backend for this model")
    return matches[0]
