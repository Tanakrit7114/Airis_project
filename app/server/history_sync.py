"""Additive, transactional history sync. No settings, credentials or deletions."""
import hashlib
import json

class SyncConflict(ValueError):
    pass

def snapshot(con):
    chats=[]
    for row in con.execute('SELECT id,title FROM chat_sessions ORDER BY id'):
        messages=[]
        for message in con.execute('SELECT * FROM chat_messages WHERE session_id=? ORDER BY id',(row['id'],)):
            meta=json.loads(message['metadata'])
            saved=meta.get('desktop_message',{})
            messages.append({**saved,'id':meta.get('sync_id','web:'+str(message['id'])),'role':message['role'],'content':message['content'],'status':saved.get('status','done')})
        chats.append({'id':row['id'],'title':row['title'],'syncTitle':row['title'],'messages':messages})
    revision=hashlib.sha256(json.dumps(chats,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {'revision':revision,'chats':chats}

def merge(db,revision,chats):
    if len(json.dumps(chats))>50_000_000 or len(chats)>1000: raise ValueError('History exceeds limit')
    with db.connect() as con:
        con.execute('BEGIN IMMEDIATE')
        before=snapshot(con)
        if before['revision']!=revision: raise SyncConflict('ประวัติบนเว็บเปลี่ยนระหว่างซิงก์ กรุณาลองใหม่')
        for chat in chats:
            cid=chat['id'];title=chat['title']
            if not isinstance(cid,str) or not cid or len(cid)>200 or not isinstance(title,str) or len(title)>120: raise ValueError('Invalid conversation')
            existing=con.execute('SELECT title FROM chat_sessions WHERE id=?',(cid,)).fetchone()
            if existing:
                baseline=chat.get('syncTitle')
                if baseline is not None and title!=baseline:
                    if existing['title'] not in (baseline,title): raise SyncConflict('ชื่อแชทถูกแก้จากทั้งสองฝั่ง: '+cid)
                    con.execute('UPDATE chat_sessions SET title=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(title,cid))
            else: con.execute('INSERT INTO chat_sessions(id,title) VALUES (?,?)',(cid,title))
            known={}
            for row in con.execute('SELECT id,role,content,metadata FROM chat_messages WHERE session_id=?',(cid,)):
                meta=json.loads(row['metadata']);known[meta.get('sync_id','web:'+str(row['id']))]=row
            for message in chat['messages']:
                mid=message['id'];role=message['role'];content=message['content']
                if not isinstance(mid,str) or len(mid)>200 or role not in ('user','assistant') or not isinstance(content,str): raise ValueError('Invalid message')
                if message.get('status')=='streaming': raise ValueError('หยุดหรือรอคำตอบก่อนซิงก์')
                if mid in known:
                    if known[mid]['content']!=content or known[mid]['role']!=role: raise SyncConflict('ข้อความขัดแย้ง ไม่เขียนทับ: '+mid)
                    continue
                con.execute('INSERT INTO chat_messages(session_id,role,content,source,route,metadata) VALUES (?,?,?,?,?,?)',
                    (cid,role,content,'desktop','sync',json.dumps({'sync_id':mid,'desktop_message':message},ensure_ascii=False)))
                known[mid]={'content':content,'role':role}
                con.execute('UPDATE chat_sessions SET updated_at=CURRENT_TIMESTAMP WHERE id=?',(cid,))
        return snapshot(con)
