import React,{useEffect,useRef,useState} from 'react'
import Icon from '../components/Icon'
import {connectChat,getSession,uploadDocument,getModels,selectModel} from '../api/client'
import MessageBubble from '../components/MessageBubble'
import TypingIndicator from '../components/TypingIndicator'
import ExtensionResult from '../components/ExtensionResult'
import {hydrateMessage,updateResponse} from '../chatState'
import '../chatFixes.css'

type Attachment={id:string,filename:string,text?:string,pages?:number,engine:string,reused?:boolean}
export default function Chat({sessionId,setSessionId}:{sessionId:string|null,setSessionId:(id:string)=>void}){
 const [messages,setMessages]=useState<any[]>([]),[input,setInput]=useState(''),[status,setStatus]=useState('พร้อมใช้งาน'),[typing,setTyping]=useState(false),[streaming,setStreaming]=useState(false),[confirm,setConfirm]=useState<any>(null),[attachment,setAttachment]=useState<Attachment|null>(null),[uploading,setUploading]=useState(false),[models,setModels]=useState<any[]>([]),[currentModel,setCurrentModel]=useState<any>(null),[switching,setSwitching]=useState(false)
 const ws=useRef<WebSocket|null>(null), fileRef=useRef<HTMLInputElement|null>(null)
 const active=useRef<string|null>(null), assignedSession=useRef<string|null>(sessionId)
 const [busy,setBusy]=useState(false),[connected,setConnected]=useState(false),[loading,setLoading]=useState(false)
 const listRef=useRef<HTMLDivElement|null>(null),followBottom=useRef(true), draft=useRef(input)
 draft.current=input
 useEffect(()=>{getModels().then(x=>{setModels(x.models||[]);setCurrentModel(x.current)}).catch(()=>{})},[])
 useEffect(()=>{
  let disposed=false, retry:ReturnType<typeof setTimeout>|undefined
  active.current=null;assignedSession.current=sessionId;setBusy(false);setTyping(false);setStreaming(false);setConfirm(null);setAttachment(null);setMessages([]);setLoading(!!sessionId);followBottom.current=true
  if(sessionId)getSession(sessionId).then(x=>{if(!disposed)setMessages((x.messages||[]).map(hydrateMessage))}).catch(()=>{if(!disposed)setStatus('โหลดประวัติไม่สำเร็จ กรุณาเปิดแชตอีกครั้ง')}).finally(()=>{if(!disposed)setLoading(false)})
  const finish=()=>{active.current=null;setBusy(false);setTyping(false);setStreaming(false);setConfirm(null)}
  const open=()=>{
   if(disposed)return
   const socket=connectChat(data=>{
    if(disposed||!active.current)return
    if(data.session_id)assignedSession.current=data.session_id
    if(data.type==='status')setStatus(data.label||data.status)
    if(data.type==='model_status')setCurrentModel(data)
    if(data.type==='typing')setTyping(!!data.active)
    if(data.type==='confirmation_request'){setConfirm(data);setTyping(false);setStreaming(false)}
    if(data.type==='token'){setTyping(false);setStreaming(true)}
    if(['token','image','extension_result','done','error'].includes(data.type)){
     const id=active.current;setMessages(m=>updateResponse(m,id,data))
    }
    if(data.type==='done'||data.type==='error'){
     finish();setStatus(data.type==='done'?'พร้อมใช้งาน':'เกิดข้อผิดพลาด');setAttachment(null)
     if(assignedSession.current)setSessionId(assignedSession.current)
    }
   },()=>{if(!disposed){setConnected(true);setStatus('พร้อมใช้งาน')}},()=>{if(!disposed)setStatus('การเชื่อมต่อมีปัญหา')})
   ws.current=socket
   socket.onclose=()=>{
    if(disposed)return
    setConnected(false)
    if(active.current){const id=active.current;setMessages(m=>updateResponse(m,id,{type:'error',message:'การเชื่อมต่อขาดหาย เปิดประวัติแชตอีกครั้งเพื่อตรวจผลก่อนส่งซ้ำ'}));finish()}
    setStatus('กำลังเชื่อมต่อใหม่…');retry=setTimeout(open,2000)
   }
  }
  open()
  return()=>{disposed=true;clearTimeout(retry);ws.current?.close();active.current=null}
 },[sessionId])
 useEffect(()=>{let live=true;const refresh=async()=>{if(!sessionId||active.current)return;try{const result=await getSession(sessionId);if(live&&!active.current)setMessages((result.messages||[]).map(hydrateMessage))}catch{}};const timer=setInterval(refresh,5000);return()=>{live=false;clearInterval(timer)}},[sessionId])
 useEffect(()=>{const list=listRef.current;if(list&&followBottom.current)list.scrollTop=list.scrollHeight},[messages,typing])
 const send=()=>{
  const text=input.trim();if(!text||active.current||switching||uploading||loading)return
  if(ws.current?.readyState!==WebSocket.OPEN){setStatus('ยังไม่ได้เชื่อมต่อ ข้อความของคุณยังอยู่ในช่องพิมพ์');return}
  const id=crypto.randomUUID();active.current=id;setBusy(true);followBottom.current=true
  setMessages(m=>[...m,{id:crypto.randomUUID(),role:'user',content:text,attachment:attachment?.filename,done:true},{id,role:'assistant',content:'',done:false}])
  try{ws.current.send(JSON.stringify({text,mode:coding?'coding':'chat',allow_cloud:cloudChat,session_id:assignedSession.current,document_id:attachment?.id||null,document_text:attachment?.text||'',attachment_filename:attachment?.filename||null}));setInput('');setTyping(true);setStreaming(false);setStatus('กำลังคิด…')}
  catch{setMessages(m=>updateResponse(m,id,{type:'error',message:'ส่งไม่สำเร็จ กรุณาลองอีกครั้ง'}));active.current=null;setBusy(false)}
 }
 const confirmAction=(approved:boolean)=>{if(ws.current?.readyState!==WebSocket.OPEN||!confirm)return;ws.current.send(JSON.stringify({type:'confirmation',session_id:confirm.session_id,approved}));setConfirm(null);setTyping(approved);setStatus(approved?'กำลังดำเนินการ…':'ยกเลิกแล้ว')}
 const [coding,setCoding]=useState(false)
 const [cloudChat,setCloudChat]=useState(()=>localStorage.getItem('airis.chat.kku-consent')==='yes')
 const [cloudOcr,setCloudOcr]=useState(()=>localStorage.getItem('airis.ocr.kku-consent')==='yes')
 const upload=async(file:File)=>{setUploading(true);setStatus('กำลังอ่านเอกสาร / OCR…');try{setAttachment(await uploadDocument(file,cloudOcr));setStatus('อ่านเอกสารสำเร็จ')}catch(e){setStatus('อัปโหลดไม่สำเร็จ');alert(e instanceof Error?e.message:'Upload failed')}finally{setUploading(false)}}
 const changeModel=async(e:React.ChangeEvent<HTMLSelectElement>)=>{const item=models.find(x=>x.id===e.target.value);if(!item||item.id===currentModel?.model)return;setSwitching(true);setStatus('กำลังโหลดโมเดล…');try{const r=await selectModel(item.id,item.backend);setCurrentModel(r)}catch(err){alert(err instanceof Error?err.message:'เปลี่ยนโมเดลไม่สำเร็จ')}finally{setSwitching(false);setStatus('พร้อมใช้งาน')}}
 return <main className="chat-page"><header><div><div className="eyebrow">AIRIS / CHAT</div><h1>Airis Universal AI</h1><div className="model-badge">{currentModel?.model||'Loading model…'} · {currentModel?.backend||'auto'}</div></div><div className="header-controls"><label className="model-select"><span>Main model</span><Icon name="chevron" size={14}/><select value={currentModel?.model||''} onChange={changeModel} disabled={switching||busy}><option value="" disabled>เลือกโมเดล</option>{models.map((m:any)=><option key={m.id} value={m.id}>{m.name}</option>)}</select></label><div className="status"><span className="dot"/>{switching?<><span className="spin-icon"><Icon name="loader" size={14}/></span>กำลังโหลดโมเดล…</>:status}</div></div></header>
 <section className="chat-wrap"><div className="messages" ref={listRef} onScroll={()=>{const list=listRef.current;if(list)followBottom.current=list.scrollHeight-list.scrollTop-list.clientHeight<100}}>{messages.length===0&&<div className="welcome"><div className="welcome-orb"/><h2>พร้อมช่วยงานของคุณ</h2><p>ถามเรื่องการเรียน งานวิชาการ การค้นข้อมูล แนบเอกสาร หรือเรียกใช้บริการที่เชื่อมต่อกับ Airis</p><div className="chips"><button onClick={()=>setInput('อธิบาย Machine Learning ให้เข้าใจง่าย')}>อธิบายวิชา</button><button onClick={()=>setInput('ช่วยวางแผนอ่านสอบให้หน่อย')}>วางแผนอ่านสอบ</button><button onClick={()=>setInput('สร้างภาพห้องเรียนมหาวิทยาลัยแห่งอนาคต')}>สร้างภาพ</button></div></div>}
 {messages.map((m,i)=><React.Fragment key={m.id||i}>{(m.content||m.done)&&<MessageBubble m={m}/>}{m.extensionResult&&<ExtensionResult result={m.extensionResult}/>} {m.image&&<div className="generated-image"><img src={m.image} alt="Airis generated"/><div className="image-actions"><a href={m.image} target="_blank" rel="noreferrer">เปิดภาพ</a><a href={m.image} download>บันทึกภาพ</a></div></div>}</React.Fragment>)}{typing&&<div className="bubble-row assistant"><div className="avatar">A</div><div className="bubble assistant typing-bubble"><div className="bubble-top"><span>Airis</span></div><TypingIndicator/></div></div>}{streaming&&!typing&&<div className="stream-cursor"/>}</div>
 <div className="composer"><label><input type="checkbox" checked={coding} disabled={busy} onChange={e=>setCoding(e.target.checked)}/> Coding mode · รัน snippets ใน Docker ก่อนแสดง (ไม่ใช่การรับรองทั้งโปรแกรม)</label><label style={{display:'block',fontSize:12,marginBottom:8}}><input type="checkbox" checked={cloudChat} onChange={e=>{setCloudChat(e.target.checked);localStorage.setItem('airis.chat.kku-consent',e.target.checked?'yes':'no')}}/> อนุญาต KKU เมื่อ Local ตอบไม่สำเร็จ (ส่งคำถาม/เอกสารออกจากเครื่อง · จำการเลือก)</label><label style={{display:'block',fontSize:12,marginBottom:8}}><input type="checkbox" checked={cloudOcr} onChange={e=>{setCloudOcr(e.target.checked);localStorage.setItem('airis.ocr.kku-consent',e.target.checked?'yes':'no')}}/> อนุญาต KKU เมื่อ Local OCR อ่านไม่ได้ (ส่งภาพ/หน้าสแกนออกจากเครื่อง · จำการเลือก · ต้องตั้ง KKU_API_KEY ที่ server)</label>{attachment&&<div className="attachment-bar"><span>{attachment.filename}{attachment.pages?` · ${attachment.pages} pages`:''} · {attachment.engine}</span><button onClick={()=>setAttachment(null)}>Remove</button></div>}<div className="composer-row"><input ref={fileRef} type="file" hidden onChange={e=>{const f=e.target.files?.[0];if(f)upload(f);e.currentTarget.value=''}}/><button className="icon-btn" onClick={()=>fileRef.current?.click()} disabled={uploading||switching||busy||loading}><Icon name="paperclip" size={18}/></button><textarea value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();send()}}} placeholder="พิมพ์ข้อความถึง Airis…" disabled={switching}/><button className="send-btn" onClick={send} disabled={uploading||switching||busy||loading||!connected||!input.trim()}><Icon name="send" size={16}/><span>ส่ง</span></button></div></div></section>
 {confirm&&<div className="confirm-modal"><div className="confirm-card"><div className="eyebrow">CONFIRM ACTION</div><h3>ยืนยันการดำเนินการ</h3><p>{confirm.description}</p><div className="confirm-actions"><button onClick={()=>confirmAction(false)}>ยกเลิก</button><button className="primary" onClick={()=>confirmAction(true)}>ยืนยัน</button></div></div></div>}
 </main>
}
