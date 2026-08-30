import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv(
    "MODEL",
    "mlx-community/Qwen3-8B-4bit"
)

SEARXNG_URL = os.getenv(
    "SEARXNG_URL",
    "http://localhost:8080"
)

MEMORY_DB = os.getenv(
    "MEMORY_DB",
    "data/jarvis.db"
)

MAX_CONTEXT_TOKENS = int(
    os.getenv("MAX_CONTEXT_TOKENS", "6000")
)

MAX_GENERATION_TOKENS = int(
    os.getenv("MAX_GENERATION_TOKENS", "512")
)

TEMPERATURE = float(
    os.getenv("TEMPERATURE", "0.3")
)

TOP_P = float(
    os.getenv("TOP_P", "0.9")
)

ENABLE_SEARCH = os.getenv(
    "ENABLE_SEARCH",
    "true"
).lower() == "true"
