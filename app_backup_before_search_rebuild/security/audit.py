from pathlib import Path
from datetime import datetime

LOG = Path("logs/audit.log")

def audit(action, status, detail=""):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(
            f"{datetime.now().isoformat()} | "
            f"{action} | {status} | {detail}\n"
        )
