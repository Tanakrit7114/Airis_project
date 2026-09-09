#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PYTHON="$ROOT/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then PYTHON="python3"; fi
export LLM_BACKEND="${LLM_BACKEND:-ollama}"
export RAG_BACKEND="${RAG_BACKEND:-$LLM_BACKEND}"
exec "$PYTHON" -m uvicorn app.server.main:app --host 127.0.0.1 --port "${PORT:-8001}"
