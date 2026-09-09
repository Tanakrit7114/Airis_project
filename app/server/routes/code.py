import asyncio
import threading
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from app.server.code_sandbox import check_answer

router=APIRouter(prefix='/api/code',tags=['code'])
class CheckRequest(BaseModel):
    answer: str = Field(max_length=128000)

@router.post('/check')
async def check(payload:CheckRequest,request:Request):
    cancel=threading.Event()
    worker=asyncio.create_task(asyncio.to_thread(check_answer,payload.answer,cancel))
    try:
        while not worker.done():
            if await request.is_disconnected():cancel.set()
            await asyncio.sleep(.1)
        return {'results':await worker,'disclaimer':'ทดสอบรัน snippet ไม่ใช่การรับรองความถูกต้องหรือความปลอดภัยของทั้งโปรแกรม'}
    finally:cancel.set()
