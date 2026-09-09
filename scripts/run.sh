#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PYTHON="$ROOT/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then PYTHON="python3"; fi
exec "$PYTHON" -m app.main
