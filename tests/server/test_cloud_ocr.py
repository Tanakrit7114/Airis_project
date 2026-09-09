import pytest
from app.documents import cloud_fallback as cloud
from app.documents import ocr

def test_no_consent_sends_nothing(monkeypatch):
    monkeypatch.setattr(cloud.requests, 'post', lambda *a, **k: pytest.fail('network'))
    with pytest.raises(RuntimeError, match='ยินยอม'):
        cloud.transcribe(b'image')

def test_quota_and_vision_fallback(monkeypatch):
    from app.images import local_vision
    monkeypatch.setattr(local_vision, 'image_payload', lambda _: 'aGVsbG8=')
    calls=[]
    class Response:
        def __init__(self, status): self.status_code=status
        def json(self): return {'choices':[{'message':{'content':'ข้อความ OCR'},'finish_reason':'stop'}]}
    def post(url, **kwargs):
        calls.append(kwargs)
        return Response(429 if len(calls)==1 else 200)
    monkeypatch.setattr(cloud.requests, 'post', post)
    with cloud.cloud_policy(True, 'test-key', ['first', 'second']):
        assert cloud.transcribe(b'image') == ('ข้อความ OCR', 'kku:second')
    assert len(calls)==2
    assert calls[0]['json']['messages']==calls[1]['json']['messages']
    with pytest.raises(RuntimeError, match='ยินยอม'): cloud.transcribe(b'image')

def test_local_success_does_not_use_cloud(monkeypatch,tmp_path):
    monkeypatch.setattr(ocr,'_local_ocr_image',lambda p:('local text','local'))
    monkeypatch.setattr(cloud,'transcribe',lambda b:pytest.fail('cloud must not run'))
    assert ocr._ocr_image(tmp_path/'unused')==('local text','local')

def test_failed_local_routes_to_cloud(monkeypatch,tmp_path):
    image=tmp_path/'image.png';image.write_bytes(b'image')
    def fail(p): raise RuntimeError('local unavailable')
    monkeypatch.setattr(ocr,'_local_ocr_image',fail)
    monkeypatch.setattr(cloud,'transcribe',lambda b:('cloud text','kku:test'))
    assert ocr._ocr_image(image)==('cloud text','kku:test')
