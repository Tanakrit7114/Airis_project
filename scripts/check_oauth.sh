#!/bin/zsh
set -e
python - <<'PY'
from dotenv import load_dotenv
import os
load_dotenv(".env", override=True)
print("JARVIS_PUBLIC_BASE_URL:", os.getenv("JARVIS_PUBLIC_BASE_URL"))
print("GOOGLE_CLIENT_ID:", os.getenv("GOOGLE_CLIENT_ID"))
print("GOOGLE_CLIENT_SECRET:", "SET" if os.getenv("GOOGLE_CLIENT_SECRET") else "EMPTY")
PY
