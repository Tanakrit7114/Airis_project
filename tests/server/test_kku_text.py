import json
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

def test_long_document_is_chunked_and_reduced(monkeypatch):
    monkeypatch.setenv('KKU_API_KEY','test-key')
    calls=[]
    class Response:
        status_code=200
        def json(self):return {'choices':[{'message':{'content':'สรุปสำเร็จ'},'finish_reason':'stop'}]}
    def post(*a,**kw):
        calls.append(kw['json']);return Response()
    monkeypatch.setattr(kku.requests,'post',post)
    document='ข้อมูลส่วนสำคัญ\n\n'*9000
    messages=[{'role':'system','content':'Answer in the user language.'},
              {'role':'user','content':json.dumps({'question':'วิเคราะห์','document':document,'sources':[]},ensure_ascii=False)}]
    result=kku.answer(messages,'test-model')
    assert 'สรุปสำเร็จ' in result
    assert len(calls)>2
    assert all(sum(len(str(m['content'])) for m in call['messages'])<kku.DIRECT_CONTEXT_LIMIT for call in calls)

def test_provider_context_error_retries_with_chunks(monkeypatch):
    monkeypatch.setenv('KKU_API_KEY','test-key')
    calls=[]
    class Response:
        status_code=200
        text=''
        def json(self):return {'choices':[{'message':{'content':'ตอบแล้ว'},'finish_reason':'stop'}]}
    def post(*a,**kw):
        calls.append(kw['json'])
        response=Response()
        if len(calls)==1:
            response.status_code=400;response.text='maximum context token length exceeded'
        return response
    monkeypatch.setattr(kku.requests,'post',post)
    payload={'question':'สรุป','document':'เนื้อหา\n\n'*6000,'sources':[]}
    result=kku.answer([{'role':'system','content':'system'}, {'role':'user','content':json.dumps(payload,ensure_ascii=False)}], 'test-model')
    assert 'ตอบแล้ว' in result
    assert len(calls)>2
