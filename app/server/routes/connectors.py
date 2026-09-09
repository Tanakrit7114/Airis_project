"""Shared Web/Desktop MCP registry; explicit manual calls, no automatic tool authority."""
import asyncio
import ipaddress
import json
import os
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

router=APIRouter(prefix='/api/connectors',tags=['connectors'])
registry=Path(os.getenv('AIRIS_MCP_REGISTRY','data/mcp-connectors.json'))
lock=asyncio.Lock()

class Connector(BaseModel):
    id: str = Field(default_factory=lambda:str(uuid.uuid4()),pattern=r'^[a-zA-Z0-9_-]{1,80}$')
    name: str = Field(min_length=1,max_length=100)
    url: str = Field(max_length=2000)
    enabled: bool = False

def validate_url(value):
    parsed=urlparse(value)
    if parsed.username or parsed.password or parsed.query or parsed.fragment: raise ValueError('ห้ามใส่ credential/query ใน URL')
    if parsed.scheme=='http' and parsed.hostname in {'localhost','127.0.0.1','::1'}:return value
    if parsed.scheme!='https' or not parsed.hostname:raise ValueError('ใช้ HTTPS หรือ HTTP loopback เท่านั้น')
    for address in socket.getaddrinfo(parsed.hostname,parsed.port or 443,type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(address[4][0]).is_global:raise ValueError('HTTPS server ต้องเป็น public address')
    return value

def load():
    try:return json.loads(registry.read_text())
    except FileNotFoundError:return []

def audit(cid,name,status):
    target=registry.with_suffix('.audit.jsonl');target.parent.mkdir(parents=True,exist_ok=True)
    with open(target,'a') as f:
        os.chmod(target,0o600)
        f.write(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'connector':cid,'tool':name,'status':status})+'\n')

@router.get('')
async def list_connectors():return load()

@router.post('')
async def save_connector(value:Connector):
    try:await asyncio.to_thread(validate_url,value.url)
    except (ValueError,OSError) as exc:raise HTTPException(400,str(exc)) from exc
    async with lock:
        rows=load();row=value.model_dump();rows=[r for r in rows if r['id']!=value.id]+[row]
        if len(rows)>30:raise HTTPException(400,'จำกัด 30 connectors')
        registry.parent.mkdir(parents=True,exist_ok=True)
        temporary=registry.with_suffix('.tmp')
        with open(temporary,'w') as f:os.chmod(temporary,0o600);json.dump(rows,f)
        temporary.replace(registry)
    return row

async def invoke(cid,name=None,arguments=None):
    row=next((r for r in load() if r['id']==cid),None)
    if not row or not row['enabled']:raise HTTPException(400,'Connector ไม่ได้เปิดใช้')
    await asyncio.to_thread(validate_url,row['url'])
    # Optional server-only token, never returned to Web/Desktop.
    token=os.getenv('AIRIS_MCP_TOKEN_'+cid.upper().replace('-','_'),'')
    headers={'Authorization':'Bearer '+token} if token else {}
    async with asyncio.timeout(30):
        async with httpx.AsyncClient(headers=headers,follow_redirects=False,timeout=20) as http:
            async with streamable_http_client(row['url'],http_client=http) as (read,write,_):
                async with ClientSession(read,write) as session:
                    await session.initialize()
                    if name is None:return (await session.list_tools()).model_dump(mode='json')
                    return (await session.call_tool(name,arguments or {})).model_dump(mode='json')

@router.get('/{cid}/tools')
async def list_tools(cid:str):
    try:return await invoke(cid)
    except HTTPException:raise
    except Exception:raise HTTPException(502,'เชื่อม MCP ไม่สำเร็จ ตรวจ URL/token/Streamable HTTP')

class ToolCall(BaseModel):
    name: str = Field(min_length=1,max_length=200)
    arguments: dict = Field(default_factory=dict)
    confirmed: bool = False

@router.post('/{cid}/call')
async def call_tool(cid:str,value:ToolCall):
    if not value.confirmed:raise HTTPException(403,'ต้องยืนยัน tool และ arguments ก่อนทุกครั้ง')
    if len(json.dumps(value.arguments))>64000:raise HTTPException(400,'Arguments เกินขีดจำกัด')
    audit(cid,value.name,'requested')
    try:
        result=await invoke(cid,value.name,value.arguments)
        audit(cid,value.name,'failed' if result.get('isError') else 'completed')
        return result
    except HTTPException:raise
    except Exception:raise HTTPException(502,'MCP tool ไม่สำเร็จ อาจเกิดผลข้างเคียงไปแล้ว ตรวจบริการก่อนเรียกซ้ำ')
