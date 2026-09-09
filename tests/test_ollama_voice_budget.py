import json
import pytest
from app.llm_backends.ollama_backend import OllamaBackend


@pytest.mark.parametrize("model,thinking", [("qwen3.6:35b-a3b-q4_K_M",False),("qwen3:14b",False),("qwen2.5-coder:7b",None)])
def test_thinking_switch_and_stream_output(monkeypatch,model,thinking):
    calls=[]
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def raise_for_status(self):pass
        def iter_lines(self,**kwargs):
            yield json.dumps({"thinking":"internal","response":""})
            yield json.dumps({"response":"four","done":True,"done_reason":"stop"})
    def post(url,**kwargs):calls.append(kwargs["json"]);return Response()
    monkeypatch.setattr("app.llm_backends.ollama_backend.requests.post",post)
    events=list(OllamaBackend(model).stream_generate("2+2",256,.3,.9))
    assert "".join(e.text for e in events)=="four"
    assert calls[0].get("think") is thinking
    assert "think" not in calls[0]["options"]
    assert events[-1].finish_reason=="stop"
