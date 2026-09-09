"""Text-only KKU fallback for an explicitly opted-in chat request."""
import os
import requests

def answer(messages):
    key=os.getenv('KKU_API_KEY','')
    if not key: raise RuntimeError('ยังไม่ได้ตั้ง KKU_API_KEY ที่ Airis server')
    if sum(len(str(m.get('content',''))) for m in messages)>120000:
        raise RuntimeError('บริบทยาวเกินขีดจำกัด กรุณาแบ่งงานก่อนส่ง KKU')
    models=os.getenv('KKU_CHAT_MODELS','gemini-3.5-flash-lite').split(',')
    for model in [m.strip() for m in models if m.strip()][:10]:
        try:
            res=requests.post('https://gen.ai.kku.ac.th/api/v1/chat/completions',headers={'Authorization':'Bearer '+key},
                json={'model':model,'messages':messages,'temperature':0.3,'max_tokens':4096,'stream':False},
                timeout=(5,90),allow_redirects=False)
        except requests.RequestException: continue
        if res.status_code in (404,429) or res.status_code>=500: continue
        if res.status_code!=200: raise RuntimeError('KKU ปฏิเสธคำขอ กรุณาตรวจ key และสิทธิ์บัญชี')
        try:
            choice=res.json()['choices'][0];text=choice['message']['content']
            if choice.get('finish_reason')=='length': continue
            if isinstance(text,str) and text.strip(): return text.strip()+'\n\n*ตอบผ่าน KKU · '+model+' · ยังไม่ได้ตรวจข้ามโมเดล*'
        except (KeyError,IndexError,TypeError,ValueError): continue
    raise RuntimeError('โมเดล KKU ที่ตั้งไว้ไม่พร้อมหรือโควตาหมด')
