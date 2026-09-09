import pytest
from app.server import kku_fallback as kku

def test_missing_key_does_not_call_network(monkeypatch):
    monkeypatch.delenv('KKU_API_KEY',raising=False)
    monkeypatch.setattr(kku.requests,'post',lambda *a,**kw:pytest.fail('network'))
    with pytest.raises(RuntimeError,match='KKU_API_KEY'):kku.answer([])

def test_text_quota_fallback_preserves_history(monkeypatch):
    monkeypatch.setenv('KKU_API_KEY','test-key');monkeypatch.setenv('KKU_CHAT_MODELS','first,second')
    calls=[]
    class Response:
        status_code=200
        def json(self):return {'choices':[{'message':{'content':'answer'},'finish_reason':'stop'}]}
    def post(*a,**kw):
        calls.append(kw['json']);result=Response();result.status_code=429 if len(calls)==1 else 200;return result
    monkeypatch.setattr(kku.requests,'post',post)
    messages=[{'role':'user','content':'question'}]
    assert 'KKU' in kku.answer(messages)
    assert calls[0]['messages']==calls[1]['messages']==messages
