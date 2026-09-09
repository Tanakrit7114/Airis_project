import asyncio
import json
import socket
import subprocess
import sys
import time
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.server.routes import connectors

def test_registry_defaults_disabled_and_calls_need_confirmation(tmp_path,monkeypatch):
    monkeypatch.setattr(connectors,'registry',tmp_path/'registry.json')
    app=FastAPI();app.include_router(connectors.router)
    with TestClient(app) as client:
        result=client.post('/api/connectors',json={'name':'test','url':'http://127.0.0.1:9999/mcp'})
        assert result.status_code==200;assert result.json()['enabled'] is False
        cid=result.json()['id']
        assert client.post('/api/connectors/'+cid+'/call',json={'name':'echo'}).status_code==403
        assert client.get('/api/connectors/'+cid+'/tools').status_code==400
        assert client.post('/api/connectors',json={'name':'bad','url':'http://169.254.169.254/mcp'}).status_code==400
        assert client.post('/api/connectors',json={'name':'bad','url':'https://user:key@example.org/mcp'}).status_code==400

def test_real_mcp_initialize_list_and_call(tmp_path,monkeypatch):
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    code=f'''from mcp.server.fastmcp import FastMCP
m=FastMCP("Airis test",host="127.0.0.1",port={port})
@m.tool()
def echo(text:str)->str:return text
m.run(transport="streamable-http")
'''
    proc=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                with socket.create_connection(('127.0.0.1',port),timeout=.1):break
            except OSError:time.sleep(.05)
        target=tmp_path/'registry.json';target.write_text(json.dumps([{'id':'test','name':'echo','url':f'http://127.0.0.1:{port}/mcp','enabled':True}]))
        monkeypatch.setattr(connectors,'registry',target)
        result=asyncio.run(connectors.invoke('test'))
        assert any(t['name']=='echo' for t in result['tools'])
        result=asyncio.run(connectors.invoke('test','echo',{'text':'Airis MCP verified'}))
        assert result['isError'] is False
        assert result['content'][0]['text']=='Airis MCP verified'
    finally:proc.terminate();proc.wait(timeout=10)
