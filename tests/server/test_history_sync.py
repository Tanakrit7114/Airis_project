import pytest
from app.server.db import DashboardDB
from app.server.history_sync import merge,snapshot,SyncConflict

def test_bidirectional_idempotent_sync_and_conflicts(tmp_path):
    db=DashboardDB(str(tmp_path/'sync.db'))
    sid=db.create_session('web title')['id']
    db.add_message(sid,'user','from web',source='general',route='chat')
    with db.connect() as con: first=snapshot(con)
    desktop={'id':'desktop-chat','title':'desktop title','messages':[{'id':'desktop-message','role':'user','content':'from desktop','status':'done','attachments':[]}]}
    merged=merge(db,first['revision'],[desktop])
    assert len(merged['chats'])==2
    assert db.list_messages('desktop-chat')[0]['content']=='from desktop'
    assert next(c for c in merged['chats'] if c['id']==sid)['messages'][0]['content']=='from web'
    again=merge(db,merged['revision'],merged['chats'])
    assert again==merged
    db.add_message(sid,'assistant','new web reply',source='general',route='chat')
    with pytest.raises(SyncConflict):merge(db,merged['revision'],[desktop])
    with db.connect() as con: fresh=snapshot(con)
    desktop['messages'][0]['content']='overwrite attempt'
    with pytest.raises(SyncConflict):merge(db,fresh['revision'],[desktop])
    assert db.list_messages('desktop-chat')[0]['content']=='from desktop'

def test_conflicting_title_rolls_back_transaction(tmp_path):
    db=DashboardDB(str(tmp_path/'sync.db'));sid=db.create_session('server title')['id']
    with db.connect() as con: first=snapshot(con)
    with pytest.raises(SyncConflict):merge(db,first['revision'],[{'id':sid,'title':'desktop edit','syncTitle':'old title','messages':[]}])
    assert db.get_session(sid)['title']=='server title'
