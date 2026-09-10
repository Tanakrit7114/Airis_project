# J.A.R.V.I.S. Local

Zero-cost, local-first AI assistant foundation.

## Initial architecture

Input -> Router -> Memory/Search -> LLM -> Response

                         |
                       Tools
                         |
                      Security

## Target stack

- Python 3.11+
- MLX-LM
- Qwen3 8B 4-bit
- SQLite + FTS5
- SearXNG
- Local-first / $0 API cost


## Airis University Web UI

### CLI

```bash
source .venv/bin/activate
./scripts/run.sh
```

### Web Dashboard + Chat

Install dependencies and build the React frontend:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cd web
npm install
npm run build
cd ..
./scripts/run_web.sh
```

Then open `http://127.0.0.1:8000`. FastAPI serves `web/dist` when it exists. API docs are available at `/docs`.

The WebSocket endpoint is `/ws/chat`. Chat/session APIs are under `/api/chat/*`; dashboard APIs are under `/api/dashboard/*`.


## Local image generation

JARVIS can generate images locally without a paid image API. The project uses MFLUX/MLX with FLUX.2 Klein 4B. Install with `pip install -r requirements.txt`. On first use, the model weights are downloaded from Hugging Face. Set `IMAGE_KEEP_LOADED=false` on a 24 GB Mac so the image model is released after each generation and JARVIS can keep the Qwen model responsive.

In Chat, prompts containing phrases such as `สร้างภาพ`, `สร้างรูป`, `วาดภาพ`, `generate an image`, or `create an image` trigger local image generation automatically.

## Extensions

JARVIS includes a local Extension manager for **Gmail, Google Drive, Google Calendar, GitHub, Notion, and Slack**. The UI is available from **Extensions** in the sidebar. Connections use OAuth and the access tokens are stored in a separate local SQLite database (`EXTENSIONS_DB`, default `data/extensions.db`).

Before clicking **Connect**, create OAuth credentials with the provider and configure the matching variables in `.env`. Use this callback pattern and register the exact URL in the provider:

```text
http://127.0.0.1:8000/api/extensions/oauth/google/callback
http://127.0.0.1:8000/api/extensions/oauth/github/callback
http://127.0.0.1:8000/api/extensions/oauth/notion/callback
```

Google uses one OAuth client but each Google Extension requests only its own read scope. After connecting, use **Test** to validate the token and **Test API** to exercise a read-only API call.

The integration layer is local-first; the JARVIS web server talks directly to each provider API only when you use that extension.
