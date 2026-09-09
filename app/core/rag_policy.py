"""Deterministic local RAG routing; never pulls missing models."""
import requests

def choose_rag_model(text, context_chars, main_model, installed):
    coding=any(word in text.lower() for word in ("code", "python", "html", "debug", "โค้ด", "โปรแกรม"))
    complex_task=context_chars>12000 or any(word in text.lower() for word in ("วิเคราะห์", "เปรียบเทียบ", "ละเอียด", "compare", "analyze"))
    preferred=("qwen2.5-coder:14b" if complex_task else "qwen2.5-coder:7b") if coding else ("qwen3.6:27b" if complex_task else "qwen3:14b")
    return preferred if preferred in installed else main_model

def installed_models():
    try:
        response=requests.get("http://127.0.0.1:11434/api/tags",timeout=2)
        response.raise_for_status()
        return {m["name"] for m in response.json().get("models",[])}
    except (requests.RequestException, ValueError, KeyError):
        return set()
