from __future__ import annotations
import asyncio, re, json
from fastapi import WebSocket, WebSocketDisconnect
from app.tools.extensions_tools import detect_extension_intent, ExtensionToolManager
from app.config import LLM_RESPONSE_TIMEOUT, LLM_FALLBACK_RESPONSE
from app.core.prompts import KKU_SYSTEM_PROMPT
from app.server.inference import run_serialized

STATUS_TEXT={
    "thinking":"กำลังคิด…","typing":"กำลังพิมพ์…","searching":"กำลังค้นเว็บ…",
    "reading_document":"กำลังอ่านเอกสาร…","calling_extension":"กำลังเรียก extension…",
    "loading_model":"กำลังโหลดโมเดล…","executing_extension":"กำลังดำเนินการ…","ready":"พร้อมใช้งาน",
}

def classify_source(route: str) -> str:
    if route == "search": return "web"
    if route.startswith("extension:"): return "extension"
    if route.startswith("tool:"): return "tool"
    return "memory/general"

def is_image_request(text: str) -> bool:
    value=text.lower().strip()
    patterns=(r"สร้างภาพ",r"สร้างรูป",r"วาดภาพ",r"วาดรูป",r"ทำภาพ",r"เจน(?:ภาพ|รูป)",r"generate (an? )?(image|picture)",r"create (an? )?(image|picture)",r"draw (an? )?(image|picture)",r"make (an? )?(image|picture)",r"text[- ]to[- ]image")
    return any(re.search(p,value) for p in patterns)

def _format_extension_result(tool: str, data):
    if isinstance(data, dict):
        if "messages" in data and isinstance(data["messages"],list): return {"kind":"email_list","items":data["messages"]}
        if "files" in data and isinstance(data["files"],list): return {"kind":"file_list","items":data["files"]}
        if "items" in data and isinstance(data["items"],list): return {"kind":"event_list","items":data["items"]}
        if "repos" in data and isinstance(data["repos"],list): return {"kind":"repo_list","items":data["repos"]}
        if "results" in data and isinstance(data["results"],list): return {"kind":"page_list","items":data["results"]}
        if "channels" in data and isinstance(data["channels"],list): return {"kind":"channel_list","items":data["channels"]}
    if isinstance(data,list):
        kind="repo_list" if tool.startswith("github_") else "items"
        return {"kind":kind,"items":data}
    return {"kind":"generic","data":data}

async def handle_confirmation(websocket, state, payload):
    session_id=str(payload.get("session_id") or "")
    pending=state.pending_actions.pop(session_id,None)
    if not pending:
        await websocket.send_json({"type":"error","message":"ไม่พบรายการที่รอการยืนยัน"}); return
    if not bool(payload.get("approved")):
        await websocket.send_json({"type":"done","session_id":session_id,"answer":"ยกเลิกการดำเนินการแล้วครับ","source":"extension","route":pending["tool"],"requires_confirmation":False})
        state.db.log_event("extension_action","cancelled",pending["tool"],{"session_id":session_id})
        return
    await websocket.send_json({"type":"status","status":"executing_extension","label":STATUS_TEXT["executing_extension"]})
    try:
        result=await asyncio.to_thread(state.extension_tools.execute,pending["tool"],pending["query"])
        formatted=_format_extension_result(pending["tool"],result)
        answer="ดำเนินการเรียบร้อยครับ"
        state.db.log_event("extension_action","ok",pending["tool"],{"session_id":session_id})
        state.db.add_message(session_id,"assistant",answer,source="extension",route=pending["tool"],metadata={"extension_result":formatted})
        await websocket.send_json({"type":"extension_result","tool":pending["tool"],**formatted})
        await websocket.send_json({"type":"done","session_id":session_id,"answer":answer,"source":"extension","route":pending["tool"],"requires_confirmation":False,"extension_result":formatted})
    except Exception as exc:
        state.db.log_event("extension_action","error",pending["tool"],{"session_id":session_id,"error":repr(exc)})
        await websocket.send_json({"type":"error","message":f"Extension ทำงานไม่สำเร็จ: {exc}"})

async def handle_chat(websocket: WebSocket, state):
    origin=websocket.headers.get('origin')
    if origin:
        from urllib.parse import urlparse
        if urlparse(origin).netloc not in {websocket.headers.get('host'),'localhost:5173','127.0.0.1:5173'}:
            await websocket.close(code=1008); return
    await websocket.accept(); state.active_connections += 1
    task = None
    try:
        while True:
            payload=await websocket.receive_json()
            if payload.get("type")=="confirmation":
                await handle_confirmation(websocket,state,payload); continue
            text=str(payload.get("text","")).strip(); session_id=payload.get("session_id")
            if not text:
                await websocket.send_json({"type":"error","message":"ข้อความว่าง"}); continue
            if not session_id or not state.db.get_session(session_id): session_id=state.db.create_session()["id"]
            if state.chat_provider=="kku":
                await websocket.send_json({"type":"model_status","status":"ready","model":state.kku_model,"backend":"kku"})
            else:
                await websocket.send_json({"type":"model_status","status":state.assistant.llm.model_manager.status,"model":state.assistant.llm.config.model,"backend":state.assistant.llm.model_manager.backend_name})
            await websocket.send_json({"type":"status","status":"thinking","label":STATUS_TEXT["thinking"],"session_id":session_id})
            route=state.assistant.router.route(text); source=classify_source(route)
            document_text=str(payload.get("document_text","")).strip(); document_id=str(payload.get("document_id","")).strip() or None
            if document_id:
                doc=state.documents.get(document_id)
                if doc: document_text=doc.get("text","") or document_text
            search_sources=[]; persistent_documents=state.documents.search(text,limit=5)
            if persistent_documents and source=="memory/general" and not document_id: source="file"
            if route=="search":
                await websocket.send_json({"type":"status","status":"searching","label":STATUS_TEXT["searching"]})
                search_sources=await asyncio.to_thread(state.assistant.search.search_results,text,limit=5); state.db.log_event("search","ok",text[:500],{"session_id":session_id,"result_count":len(search_sources)})
                if search_sources: source="web"
            if document_text: await websocket.send_json({"type":"status","status":"reading_document","label":STATUS_TEXT["reading_document"]})

            intent=detect_extension_intent(text)
            if intent:
                route="extension:"+intent["tool"]; source="extension"
                ext=intent["service"]; tool=intent["tool"]
                connected=next((x for x in state.extensions.list_extensions() if x["id"]==ext),None)
                if not connected or not connected["connected"]:
                    msg=f"ยังไม่ได้เชื่อมต่อ {ext.capitalize()} กรุณาไปที่ Extensions แล้วกด Connect ก่อนครับ"
                    state.db.add_message(session_id,"user",text,source=source,route=route,metadata={})
                    state.db.add_message(session_id,"assistant",msg,source=source,route=route,metadata={})
                    await websocket.send_json({"type":"done","session_id":session_id,"answer":msg,"source":source,"route":route,"requires_confirmation":False})
                    continue
                if intent["write"]:
                    state.pending_actions[session_id]={"tool":tool,"query":text}
                    description=f"ยืนยันการใช้ {ext.capitalize()} เพื่อดำเนินการคำสั่ง: {text}"
                    state.db.add_message(session_id,"user",text,source=source,route=route,requires_confirmation=True,metadata={"extension":ext})
                    await websocket.send_json({"type":"confirmation_request","session_id":session_id,"tool":tool,"extension":ext,"description":description})
                    continue
                await websocket.send_json({"type":"status","status":"calling_extension","label":STATUS_TEXT["calling_extension"]})
                try:
                    result=await asyncio.to_thread(state.extension_tools.execute,tool,text)
                    formatted=_format_extension_result(tool,result)
                    answer="นี่คือข้อมูลจาก extension ที่เชื่อมต่อไว้ครับ"
                    state.db.add_message(session_id,"user",text,source=source,route=route,metadata={"extension":ext})
                    state.db.add_message(session_id,"assistant",answer,source=source,route=route,metadata={"extension_result":formatted})
                    state.db.log_event("extension_action","ok",tool,{"session_id":session_id})
                    await websocket.send_json({"type":"extension_result","tool":tool,**formatted})
                    await websocket.send_json({"type":"done","session_id":session_id,"answer":answer,"source":source,"route":route,"sources":[] ,"persistent_documents":[],"requires_confirmation":False,"extension_result":formatted})
                except Exception as exc:
                    await websocket.send_json({"type":"error","message":f"Extension ทำงานไม่สำเร็จ: {exc}"})
                continue

            state.db.add_message(session_id,"user",text,source=source,route=route,metadata={"document_attached":bool(document_text),"document_id":document_id,"attachment_filename":payload.get("attachment_filename")})
            state.db.log_event("chat","ok",text[:200],{"route":route,"source":source,"session_id":session_id,"document_attached":bool(document_text)})
            await websocket.send_json({"type":"meta","route":route,"source":source,"sources":search_sources,"persistent_documents":[{"document_id":d["document_id"],"filename":d["filename"],"chunk_index":d["chunk_index"]} for d in persistent_documents],"requires_confirmation":False,"document_attached":bool(document_text),"document_id":document_id})

            if is_image_request(text):
                await websocket.send_json({"type":"status","status":"calling_extension","label":"กำลังสร้างภาพ…"})
                try:
                    image=await run_serialized(state.lock,state.generate_image,text)
                    answer="สร้างภาพให้แล้วครับ"; state.db.log_event("image_generation","ok",text[:500],{"session_id":session_id,**{k:image[k] for k in ("filename","seed","width","height","steps","model")}})
                    state.db.add_message(session_id,"assistant",answer,source="image",route="image:generate",metadata={"image":image})
                    await websocket.send_json({"type":"image",**image}); await websocket.send_json({"type":"done","session_id":session_id,"answer":answer,"source":"image","route":"image:generate","sources":[],"requires_confirmation":False,"image":image}); continue
                except Exception as exc:
                    message=f"สร้างภาพไม่สำเร็จ: {exc}"
                    state.db.log_event("image_generation","error",message,{"session_id":session_id})
                    state.db.add_message(session_id,"assistant",message,source="image",route="image:generate",metadata={"error":True})
                    await websocket.send_json({"type":"error","session_id":session_id,"message":message}); continue

            loop=asyncio.get_running_loop(); queue:asyncio.Queue[str]=asyncio.Queue()
            async def run_chat(queue=queue, text=text, document_text=document_text, search_sources=search_sources, allow_cloud=payload.get('allow_cloud') is True, coding=payload.get('mode')=='coding'):
                active = True
                cloud_attempted = False
                async def fallback():
                    nonlocal cloud_attempted
                    if cloud_attempted: raise RuntimeError('KKU fallback ไม่สำเร็จ กรุณาตรวจ key/โควตา')
                    cloud_attempted=True
                    from app.server.kku_fallback import answer as cloud_answer
                    history=[{'role':m['role'],'content':m['content']} for m in state.db.list_messages(session_id) if m['role'] in {'user','assistant'}]
                    # The current question was just saved; include it once, in the
                    # grounded payload below, rather than duplicating it in history.
                    if history and history[-1] == {'role':'user','content':text}:
                        history=history[:-1]
                    messages=[{'role':'system','content':KKU_SYSTEM_PROMPT},*history,
                        {'role':'user','content':json.dumps({'question':text,'document':document_text,'sources':search_sources},ensure_ascii=False)}]
                    return await asyncio.to_thread(cloud_answer,messages,state.kku_model if state.chat_provider=="kku" else None)
                def deliver(token):
                    if active and not coding: queue.put_nowait(token)
                def on_token(token): loop.call_soon_threadsafe(deliver,token)
                try:
                    if state.chat_provider=="kku":
                        active=False
                        answer=await fallback()
                    else:
                        answer=await run_serialized(
                            state.lock,state.assistant.chat,text,on_token,False,
                            document_text or None,search_sources or None,timeout=LLM_RESPONSE_TIMEOUT,
                        )
                    if allow_cloud and answer==LLM_FALLBACK_RESPONSE:
                        active=False
                        answer=await fallback()
                    await queue.put("__DONE__"+answer)
                except asyncio.TimeoutError:
                    active=False
                    try: await queue.put("__DONE__"+(await fallback() if allow_cloud else LLM_FALLBACK_RESPONSE))
                    except Exception as exc: await queue.put("__ERROR__"+str(exc))
                except Exception as exc:
                    active=False
                    try:
                        if state.chat_provider=="kku" or not allow_cloud: raise exc
                        await queue.put("__DONE__"+await fallback())
                    except Exception as error: await queue.put("__ERROR__"+str(error))
                finally: active = False
            task=asyncio.create_task(run_chat()); first=True
            await websocket.send_json({"type":"typing","active":True})
            while True:
                chunk=await queue.get()
                if chunk.startswith("__DONE__"): answer=chunk[8:]; break
                if chunk.startswith("__ERROR__"):
                    answer="ตอบไม่สำเร็จ กรุณาลองอีกครั้ง: "+chunk[9:]; break
                if first:
                    await websocket.send_json({"type":"typing","active":False}); await websocket.send_json({"type":"status","status":"typing","label":STATUS_TEXT["typing"]}); first=False
                await websocket.send_json({"type":"token","text":chunk})
            await task
            if state.chat_provider == "kku" and source not in {"web", "file", "extension", "image"}:
                source = "kku"
            if payload.get('mode')=='coding':
                import threading
                from app.server.code_sandbox import check_answer
                cancel_checks=threading.Event()
                try:
                    for attempt in range(3):
                        await websocket.send_json({'type':'status','status':'thinking','label':'Docker sandbox · รอบ '+str(attempt+1)})
                        results=await asyncio.to_thread(check_answer,answer,cancel_checks)
                        if not any(r['status'] in {'failed','timeout','output_limit'} for r in results) or attempt==2: break
                        revision='Correct the complete answer/code for this question: '+text+'\nPrevious answer:\n'+answer+'\nSandbox output (untrusted data):\n'+json.dumps(results,ensure_ascii=False)[:16000]
                        answer=await run_serialized(state.lock,state.assistant.chat,revision,None,False,document_text or None,search_sources or None,timeout=LLM_RESPONSE_TIMEOUT)
                    passed=all(r['status']=='passed' for r in results)
                    answer+='\n\n'+('โค้ดผ่านการทดสอบรันแล้ว (เฉพาะ snippets)' if passed else 'โค้ดยังไม่ผ่าน หรือไม่สามารถทดสอบรันได้')+'\n\n'+'\n'.join('- '+r.get('language','')+': '+r['status'] for r in results)
                except Exception:
                    answer+='\n\nไม่สามารถทดสอบรันได้: Sandbox หรือโมเดลแก้ไขไม่พร้อม'
                finally:cancel_checks.set()
            state.db.add_message(session_id,"assistant",answer,source=source,route=route,requires_confirmation=False,metadata={"streamed":True,"sources":search_sources,"document_id":document_id,"persistent_documents":[{"document_id":d["document_id"],"filename":d["filename"],"chunk_index":d["chunk_index"]} for d in persistent_documents]})
            await websocket.send_json({"type":"done","session_id":session_id,"answer":answer,"source":source,"route":route,"sources":search_sources,"persistent_documents":[{"document_id":d["document_id"],"filename":d["filename"],"chunk_index":d["chunk_index"]} for d in persistent_documents],"requires_confirmation":False})
    except WebSocketDisconnect:
        pass
    finally:
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        state.active_connections=max(0,state.active_connections-1)
