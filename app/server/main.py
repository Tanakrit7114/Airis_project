from pathlib import Path
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import IMAGE_HEIGHT, IMAGE_KEEP_LOADED, IMAGE_MODEL, IMAGE_OUTPUT_DIR, IMAGE_QUANTIZE, IMAGE_STEPS, IMAGE_WIDTH
from app.images.generator import LocalImageGenerator

from app.core.assistant import Assistant
from app.documents.store import DocumentStore
from app.server.db import DashboardDB
from app.server.routes.chat import router as chat_router
from app.server.routes.dashboard import router as dashboard_router
from app.server.routes.documents import router as documents_router
from app.server.routes.images import router as images_router
from app.server.routes.models import router as models_router
from app.tools.extensions_tools import ExtensionToolManager
from app.server.ws_chat import handle_chat
from app.extensions.manager import ExtensionManager


class ServerState:
    def generate_image(self, prompt, **options):
        # Called under the shared inference lock by both HTTP and WebSocket.
        # MLX text models otherwise occupy unified memory during FLUX generation.
        for engine in (self.assistant.llm, self.assistant.rag_llm):
            if engine.model_manager.backend_name in {"mlx", "llama.cpp"}:
                engine.model_manager.unload()
        return self.image_generator.generate(prompt, **options)

    def __init__(self):
        self.assistant = Assistant()
        self.db = DashboardDB()
        self.documents = DocumentStore()
        self.image_generator = LocalImageGenerator(
            output_dir=IMAGE_OUTPUT_DIR,
            model_name=IMAGE_MODEL,
            steps=IMAGE_STEPS,
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT,
            quantize=IMAGE_QUANTIZE,
            keep_loaded=IMAGE_KEEP_LOADED,
        )
        self.active_connections = 0
        self.lock = asyncio.Lock()
        self.model_lock = asyncio.Lock()
        self.extensions = ExtensionManager()
        self.extension_tools = ExtensionToolManager(self.extensions)
        self.pending_actions = {}
        self.chat_provider = "local"
        self.kku_model = None
        self.assistant.extension_manager = self.extensions
        for tool_name in [
            "gmail_search","gmail_read","gmail_send","gmail_news_report","gmail_trash","drive_search","drive_read_file","drive_create_file","drive_update_file","drive_delete_file",
            "calendar_list_events","calendar_create_event","calendar_update_event","calendar_delete_event","github_list_repos","github_read_file","github_create_issue","github_update_issue","github_close_issue",
            "notion_search","notion_read_page","notion_update_page","notion_archive_page",
        ]:
            self.assistant.tool_registry.register(tool_name, lambda *args, _n=tool_name, **kwargs: self.extension_tools.execute(_n,*args,**kwargs), "JARVIS extension tool; use only when the corresponding extension is connected.")


state = ServerState()
app = FastAPI(title="Airis Universal AI", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8001", "http://localhost:8001", "http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router)
from app.server.routes.code import router as code_router
app.include_router(code_router)
from app.server.routes.connectors import router as connectors_router
app.include_router(connectors_router)
app.include_router(dashboard_router)
app.include_router(documents_router)
app.include_router(images_router)
app.include_router(models_router)

@app.middleware("http")
async def protect_local_writes(request, call_next):
    origin = request.headers.get("origin")
    if request.method not in {"GET", "HEAD", "OPTIONS"} and origin:
        from urllib.parse import urlparse
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or parsed.netloc not in {request.url.netloc, "127.0.0.1:5173", "localhost:5173"}:
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Untrusted origin"}, status_code=403)
    return await call_next(request)
from app.server.routes.operator import router as operator_router
app.include_router(operator_router)
from app.server.routes.extensions import router as extensions_router
app.include_router(extensions_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "airis", "model": state.assistant.llm.config.model}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    # MLX generation is local/single-model; serialize generation to avoid model contention.
    await handle_chat(websocket, state)


@app.get("/generated/{filename}")
def generated_image(filename: str):
    from fastapi import HTTPException

    base = Path(IMAGE_OUTPUT_DIR).resolve()
    target = (base / Path(filename).name).resolve()
    if base not in target.parents or not target.is_file():
        raise HTTPException(404, "Image not found")
    return FileResponse(target)


web_dist = Path(__file__).resolve().parents[2] / "web" / "dist"
if web_dist.exists():
    app.mount("/assets", StaticFiles(directory=web_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def frontend(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            return {"detail": "Not found"}
        target = (web_dist / full_path).resolve()
        if not target.is_relative_to(web_dist.resolve()):
            from fastapi import HTTPException
            raise HTTPException(404, 'Not found')
        if target.is_file():
            return FileResponse(target)
        return FileResponse(web_dist / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "service": "Airis Universal AI API",
            "status": "ok",
            "frontend": "React build not found. Run: cd web && npm install && npm run build",
            "docs": "/docs",
        }


@app.on_event("shutdown")
def shutdown():
    state.assistant.shutdown()
