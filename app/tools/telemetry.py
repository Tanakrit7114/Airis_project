"""Read-only, bounded Apple Silicon telemetry. Never synthesize sensor values."""
import json
import math
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone

_lock=threading.Lock()
_cache={}
_at=0.0

def number(value,low,high):
    return round(value,2) if isinstance(value,(int,float)) and math.isfinite(value) and low<=value<=high else None

def normalize(raw):
    temp=raw.get("temp",{})
    memory=raw.get("memory",{})
    cpu=number(raw.get("cpu_active_ratio"),0,1)
    gpu=number(raw.get("gpu_active_ratio"),0,1)
    return {"available":True,"source":"macmon / Apple Silicon sensors","timestamp":raw.get("timestamp"),
        "cpu_percent":None if cpu is None else round(cpu*100,1),"gpu_percent":None if gpu is None else round(gpu*100,1),
        "cpu_celsius":number(temp.get("cpu_temp_avg"),1,130),"gpu_celsius":number(temp.get("gpu_temp_avg"),1,130),
        "ram_used_gb":round(memory.get("ram_usage",0)/1024**3,2),"ram_total_gb":round(memory.get("ram_total",0)/1024**3,2),
        "swap_used_gb":round(memory.get("swap_usage",0)/1024**3,2),"system_watts":number(raw.get("sys_power"),0,1000)}

def snapshot():
    global _cache,_at
    with _lock:
        if time.monotonic()-_at<2:return dict(_cache)
        try:
            binary=shutil.which("macmon") or "/opt/homebrew/bin/macmon"
            result=subprocess.run([binary,"pipe","-s","1","-i","500"],capture_output=True,text=True,timeout=4,check=True)
            _cache=normalize(json.loads(result.stdout.strip().splitlines()[-1]))
        except (OSError,subprocess.SubprocessError,ValueError,IndexError) as exc:
            _cache={"available":False,"source":"macmon","reason":"Sensor unavailable: "+type(exc).__name__,"timestamp":datetime.now(timezone.utc).isoformat()}
        _at=time.monotonic()
        return dict(_cache)
