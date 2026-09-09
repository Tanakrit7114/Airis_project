#!/bin/bash
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate
pip install -r requirements.txt
if ! command -v npm >/dev/null 2>&1; then
  echo "Node.js/npm is required for the React frontend. Backend can still run with scripts/run_web.sh."
  exit 0
fi
cd web
npm install
npm run build
