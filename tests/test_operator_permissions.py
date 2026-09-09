import time
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.server.routes.operator import router, search_local_files
from app.core.rag_policy import choose_rag_model

@pytest.fixture
def client():
    app=FastAPI();app.include_router(router)
    return TestClient(app)

def test_session_and_revocation(client):
    assert client.post("/api/operator/command",json={"text":"open app Calculator"}).status_code==401
    token=client.post("/api/operator/session",json={"permissions":[]}).json()["token"]
    h={"X-Operator-Session":token}
    assert client.post("/api/operator/command",json={"text":"open app Calculator"},headers=h).status_code==403
    assert client.post("/api/operator/command",json={"text":"delete file anything"},headers=h).json()["source"]=="permission policy"
    client.delete("/api/operator/session",headers=h)
    assert client.post("/api/operator/command",json={"text":"start task example"},headers=h).status_code==401

def test_cross_origin_denied(client):
    assert client.post("/api/operator/session",json={"permissions":[]},headers={"Origin":"https://attacker.example"}).status_code==403

def test_file_scope(tmp_path):
    (tmp_path/"budget.txt").touch()
    (tmp_path/"budget-link").symlink_to("/etc/passwd")
    item={"permissions":{"files"},"root":tmp_path,"expires":time.monotonic()+60}
    assert [x["title"] for x in search_local_files(item,"budget")]==["budget.txt"]
    item["permissions"]=set()
    with pytest.raises(HTTPException):search_local_files(item,"budget")

def test_auto_rag_selection():
    assert choose_rag_model("debug python",2000,"main",{"qwen2.5-coder:7b"})=="qwen2.5-coder:7b"
    assert choose_rag_model("วิเคราะห์",20000,"main",{"qwen3.6:27b"})=="qwen3.6:27b"
    assert choose_rag_model("สรุป",100,"main",set())=="main"


def test_general_answer_uses_selected_engine(client,monkeypatch):
    import asyncio
    import sys
    from types import SimpleNamespace
    calls=[]
    def stream(messages,**kwargs):
        calls.append((messages,kwargs))
        return "คำตอบทดสอบ"
    fake=SimpleNamespace(state=SimpleNamespace(lock=asyncio.Lock(),assistant=SimpleNamespace(
        llm=SimpleNamespace(stream=stream,config=SimpleNamespace(timeout=1)))))
    monkeypatch.setitem(sys.modules,"app.server.main",fake)
    token=client.post("/api/operator/session",json={"permissions":[]}).json()["token"]
    response=client.post("/api/operator/command",json={"text":"อธิบายแรงโน้มถ่วง"},headers={"X-Operator-Session":token})
    assert response.status_code==200
    assert response.json()["answer"]=="คำตอบทดสอบ"
    assert calls[0][1]=={"max_tokens":256,"emit_console":False}
