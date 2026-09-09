import asyncio
import threading
from types import SimpleNamespace

from fastapi import WebSocketDisconnect
from app.server import ws_chat


def test_late_tokens_cannot_enter_next_chat(monkeypatch):
    async def scenario():
        release=threading.Event()
        class DB:
            def get_session(self, sid): return True
            def add_message(self,*args,**kwargs): pass
            def log_event(self,*args,**kwargs): pass
        class Socket:
            headers={}
            sent=[]
            count=0
            async def accept(self): pass
            async def receive_json(self):
                self.count+=1
                if self.count>2: raise WebSocketDisconnect()
                if self.count==2: release.set()
                return {"text":f"question {self.count}","session_id":"test"}
            async def send_json(self,data): self.sent.append(data)
        def chat(text,on_token,*args):
            if text=="question 1":
                release.wait(2)
                on_token("STALE TOKEN")
                return "STALE ANSWER"
            on_token("CURRENT TOKEN")
            return "CURRENT ANSWER"
        state=SimpleNamespace(
            active_connections=0,lock=asyncio.Lock(),db=DB(),
            documents=SimpleNamespace(search=lambda *a,**k:[]),
            assistant=SimpleNamespace(
                chat=chat,router=SimpleNamespace(route=lambda _:"general"),
                llm=SimpleNamespace(config=SimpleNamespace(model="test"),
                    model_manager=SimpleNamespace(status="ready",backend_name="fake"))))
        socket=Socket()
        try:
            await asyncio.wait_for(ws_chat.handle_chat(socket,state),2)
        finally: release.set()
        tokens=[m["text"] for m in socket.sent if m["type"]=="token"]
        answers=[m["answer"] for m in socket.sent if m["type"]=="done"]
        assert tokens==["CURRENT TOKEN"]
        assert answers==[ws_chat.LLM_FALLBACK_RESPONSE,"CURRENT ANSWER"]
        assert state.active_connections==0
        assert not state.lock.locked()
    monkeypatch.setattr(ws_chat,"LLM_RESPONSE_TIMEOUT",.05)
    asyncio.run(scenario())
