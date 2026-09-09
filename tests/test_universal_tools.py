import time
from pathlib import Path
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.server.routes.operator import router, file_action

def test_web_requires_permission():
    app=FastAPI();app.include_router(router);client=TestClient(app)
    token=client.post("/api/operator/session",json={"permissions":[]}).json()["token"]
    assert client.post("/api/operator/command",json={"text":"ค้นเว็บ Python"},headers={"X-Operator-Session":token}).status_code==403

def test_control_requires_bound_confirmation():
    app=FastAPI();app.include_router(router);client=TestClient(app)
    token=client.post("/api/operator/session",json={"permissions":["system"]}).json()["token"]
    h={"X-Operator-Session":token}
    with patch("app.server.routes.operator.installed_apps",return_value=[Path("/Applications/Notes.app")]),patch("app.tools.desktop_control.control_app",return_value={"app":"Notes","action":"type"}) as control:
        r=client.post("/api/operator/command",json={"text":'control app {"app":"Notes","action":"type","value":"hello"}'},headers=h)
        assert r.json()["source"]=="confirmation required"
        control.assert_not_called()
        assert client.post("/api/operator/command",json={"text":"ยืนยัน"},headers=h).status_code==200
        control.assert_called_once_with("Notes","type","hello")

def test_read_file_scope(tmp_path):
    p=tmp_path/"a.txt";p.write_text("hello")
    result=file_action({"permissions":{"files"},"root":tmp_path,"expires":time.monotonic()+30},"read",str(p))
    assert result["results"][0]["content"]=="hello"
