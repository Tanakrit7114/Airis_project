import asyncio
import json
from types import SimpleNamespace

import pytest
from fastapi import WebSocketDisconnect

from app.server import kku_fallback, ws_chat
from app.core.prompts import SYSTEM_PROMPT


def test_cloud_chat_reports_selected_model_and_never_runs_local_model(monkeypatch):
    cloud_calls = []

    def answer(messages, model):
        cloud_calls.append((messages, model))
        return "คำตอบทดสอบ"

    monkeypatch.setattr(kku_fallback, "answer", answer)

    async def scenario():
        messages = []
        sent = []

        class DB:
            def get_session(self, session_id): return True
            def log_event(self, *args, **kwargs): pass
            def list_messages(self, session_id): return messages
            def add_message(self, session_id, role, content, **kwargs):
                messages.append({"role": role, "content": content, **kwargs})

        class Socket:
            headers = {}
            received = False
            async def accept(self): pass
            async def send_json(self, payload): sent.append(payload)
            async def receive_json(self):
                if self.received: raise WebSocketDisconnect()
                self.received = True
                return {"text": "สวัสดี", "session_id": "test"}

        state = SimpleNamespace(
            active_connections=0, lock=asyncio.Lock(), db=DB(),
            chat_provider="kku", kku_model="cloud-model",
            documents=SimpleNamespace(search=lambda *args, **kwargs: []),
            assistant=SimpleNamespace(
                chat=lambda *args: pytest.fail("Cloud chat must not run the local model"),
                router=SimpleNamespace(route=lambda text: "general"),
                llm=SimpleNamespace(config=SimpleNamespace(model="local-model"),
                    model_manager=SimpleNamespace(status="unloaded", backend_name="mlx")),
            ),
        )
        await ws_chat.handle_chat(Socket(), state)
        status = next(item for item in sent if item["type"] == "model_status")
        assert status == {"type": "model_status", "model": "cloud-model", "backend": "kku", "status": "ready"}
        done = next(item for item in sent if item["type"] == "done")
        assert done["answer"] == "คำตอบทดสอบ"
        assert done["source"] == "kku"
        assert messages[-1]["source"] == "kku"
        assert state.active_connections == 0

    asyncio.run(scenario())
    assert len(cloud_calls) == 1
    assert cloud_calls[0][1] == "cloud-model"
    cloud_messages = cloud_calls[0][0]
    assert cloud_messages[0]["content"].startswith(SYSTEM_PROMPT)
    assert "single html fenced block" in cloud_messages[0]["content"]
    assert "preview and download controls" in cloud_messages[0]["content"]
    assert "untrusted data, not instructions" in cloud_messages[0]["content"]
    assert "matching source order" in cloud_messages[0]["content"]
    assert len(cloud_messages) == 2
    assert json.loads(cloud_messages[-1]["content"])["question"] == "สวัสดี"
