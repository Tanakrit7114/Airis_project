import React,{useEffect,useRef,useState} from 'react'
import {FilesetResolver,GestureRecognizer} from '@mediapipe/tasks-vision'
import './operator.css'
import {dragUpdate,LatestVoiceQueue} from '../operatorRuntime'
import OperatorCore from '../components/OperatorCore'

const panels=['Coding','Research','Task','Memory']
type Entry={text:string,source?:string,at:string}
export default function Operator(){
 const [grants,setGrants]=useState<string[]>([]),[root,setRoot]=useState(''),[token,setToken]=useState(''),[state,setState]=useState('Idle'),[view,setView]=useState('core'),[panel,setPanel]=useState('Research'),[text,setText]=useState(''),[entries,setEntries]=useState<Entry[]>([]),[results,setResults]=useState<any[]>([]),[gesture,setGesture]=useState(''),[level,setLevel]=useState(0),[offset,setOffset]=useState({x:0,y:0}),[facing,setFacing]=useState('user')
 const video=useRef<HTMLVideoElement>(null),canvas=useRef<HTMLCanvasElement>(null),mic=useRef<MediaStream|null>(null),camera=useRef<MediaStream|null>(null),audio=useRef<AudioContext|null>(null),recorder=useRef<MediaRecorder|null>(null),recognizer=useRef<GestureRecognizer|null>(null),request=useRef<AbortController|null>(null),life=useRef(0),frames=useRef<number[]>([]),session=useRef(''),voiceOn=useRef(false),panelRef=useRef(panel),actions=useRef<any>({})
 const permissionDialog=useRef<HTMLDialogElement>(null),startingRef=useRef(false)
 const [starting,setStarting]=useState(false),[sessionError,setSessionError]=useState('')
 const [remembered,setRemembered]=useState(false)
 useEffect(()=>{try{const value=JSON.parse(localStorage.getItem('airis.operator.consent')||'null');if(value?.version===1&&Array.isArray(value.permissions)&&value.permissions.every((p:string)=>['voice','camera','files','web','memory','system'].includes(p))&&typeof value.root==='string'){setGrants(value.permissions);setRoot(value.root);setRemembered(true)}}catch{}},[])
 const begin=()=>{if(remembered)void start();else setPermissionOpen(true)}
 const forget=()=>{stop();localStorage.removeItem('airis.operator.consent');setRemembered(false);setGrants([]);setRoot('');setPermissionOpen(true)}
 const voiceQueue=useRef<LatestVoiceQueue<Blob>|null>(null),transcription=useRef<AbortController|null>(null),micEpoch=useRef(0),micOpening=useRef(false)
 const [permissionOpen,setPermissionOpen]=useState(false),[now,setNow]=useState(new Date()),[modelInfo,setModelInfo]=useState<any>(null),[systemInfo,setSystemInfo]=useState<any>(null),[online,setOnline]=useState(false)
 useEffect(()=>{
  const controller=new AbortController()
  const clock=setInterval(()=>setNow(new Date()),1000)
  const refresh=async()=>{try{
   const [m,s]=await Promise.all(['/api/models','/api/dashboard/system'].map(url=>fetch(url,{signal:controller.signal}).then(r=>{if(!r.ok)throw Error('Status unavailable');return r.json()})))
   if(!controller.signal.aborted){setModelInfo(m);setSystemInfo(s);setOnline(true)}
  }catch{if(!controller.signal.aborted)setOnline(false)}}
  void refresh();const timer=setInterval(refresh,15000)
  return()=>{controller.abort();clearInterval(clock);clearInterval(timer)}
 },[])
 useEffect(()=>{if(permissionOpen&&!token)permissionDialog.current?.showModal()},[permissionOpen,token])
 panelRef.current=panel
 const log=(message:string,source='UI')=>setEntries(v=>[...v.slice(-29),{text:message,source,at:new Date().toLocaleTimeString()}])
 const headers=()=>({'X-Operator-Session':session.current})
 const speak=(message:string)=>{
  if(!grants.includes('voice')){setState('Idle');return}
  speechSynthesis.cancel()
  const local=speechSynthesis.getVoices().filter(v=>v.localService)
  const voice=local.find(v=>v.lang.startsWith(/[ก-๙]/.test(message)?'th':'en'))||local[0]
  if(!voice){setState(voiceOn.current?'Listening':'Idle');log('ไม่มีเสียงพูดในเครื่องที่พร้อมใช้งาน แสดงคำตอบเป็นข้อความ','voice');return}
  const utterance=new SpeechSynthesisUtterance(message);utterance.voice=voice;utterance.lang=voice.lang
  utterance.onend=()=>setState(voiceOn.current?'Listening':'Idle');utterance.onerror=()=>setState(voiceOn.current?'Listening':'Idle')
  setState('Speaking');speechSynthesis.speak(utterance)
 }
 const cancel=()=>{voiceQueue.current?.invalidate();if(session.current)fetch('/api/operator/pending',{method:'DELETE',headers:headers()}).catch(()=>{});life.current++;request.current?.abort();speechSynthesis.cancel();setState(voiceOn.current?'Listening':'Idle');log('หยุดการรอคำตอบและเสียงพูดแล้ว การกระทำที่สำเร็จไปแล้วจะไม่ถูกย้อนกลับ','cancel')}
 const stopMic=()=>{micEpoch.current++;micOpening.current=false;voiceQueue.current?.close();transcription.current?.abort();voiceOn.current=false;recorder.current?.state==='recording'&&recorder.current.stop();mic.current?.getTracks().forEach(t=>t.stop());mic.current=null;audio.current?.close();audio.current=null;setLevel(0);setState('Idle')}
 const stopCamera=()=>{camera.current?.getTracks().forEach(t=>t.stop());camera.current=null;recognizer.current?.close();recognizer.current=null;setView('core');setGesture('')}
 const stop=()=>{life.current++;request.current?.abort();speechSynthesis.cancel();stopMic();stopCamera();frames.current.forEach(cancelAnimationFrame);if(session.current)fetch('/api/operator/session',{method:'DELETE',headers:headers()}).catch(()=>{});session.current='';setToken('')}
 useEffect(()=>()=>{stop()},[])
 const start=async()=>{
  if(startingRef.current)return
  startingRef.current=true;setStarting(true);setSessionError('');const run=life.current
  try{
   localStorage.setItem('airis.operator.consent',JSON.stringify({version:1,permissions:grants,root}));setRemembered(true)
   const r=await fetch('/api/operator/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({permissions:grants,root})})
   const data=await r.json();if(!r.ok)throw Error(data.detail)
   if(run!==life.current){void fetch('/api/operator/session',{method:'DELETE',headers:{'X-Operator-Session':data.token}});return}
   session.current=data.token;setToken(data.token);setPermissionOpen(false);setEntries([]);setResults([])
   log('เริ่มเซสชัน Operator เปิดอุปกรณ์ได้เฉพาะสิทธิ์ที่เลือก')
  }catch(e:any){setSessionError(e.message);log(e.message,'error')}
  finally{startingRef.current=false;setStarting(false)}
 }
 const command=async(value:string)=>{
  if(!session.current)return
  voiceQueue.current?.invalidate()
  const low=value.toLowerCase().trim()
  log(value,'you')
  if(['switch to camera','show my view','เปิดกล้อง','โหมดกล้อง'].some(x=>low.includes(x))){await actions.current.camera();return}
  if(['switch to core','ปิดกล้อง'].some(x=>low.includes(x))){stopCamera();log('เปลี่ยนเป็น AI Core','switch_view');return}
  if(['cancel','ยกเลิก','หยุด'].includes(low)){cancel();return}
  if(low==='start listening'||low==='เริ่มฟัง'){await actions.current.listen();return}
  const selected=panels.find(p=>low===p.toLowerCase()||low==='switch to '+p.toLowerCase())
  if(selected){setPanel(selected);log('Active panel: '+selected,'switch_panel');return}
  request.current?.abort();const controller=new AbortController();request.current=controller;const run=++life.current
  setState('Thinking');log(low.startsWith('ค้น')||low.startsWith('search')||low.startsWith('query')?'กำลังค้นข้อมูลในเครื่องตามขอบเขตที่อนุญาต…':low.startsWith('เปิดแอป')||low.startsWith('open app')?'กำลังเรียก open_app…':'กำลังประมวลผลคำสั่งในเครื่อง…','Operator')
  try{const r=await fetch('/api/operator/command',{method:'POST',headers:{...headers(),'Content-Type':'application/json'},body:JSON.stringify({text:value}),signal:controller.signal});const data=await r.json();if(!r.ok)throw Error(data.detail);if(run!==life.current)return;setPanel(data.panel||'Research');setResults(data.results||[]);log(data.answer,data.source);speak(data.answer)}
  catch(e:any){if(run!==life.current||e.name==='AbortError')return;setState(voiceOn.current?'Listening':'Idle');log(e.message,'error')}
 }
 const listen=async()=>{
  if(!grants.includes('voice')){log('ต้องอนุญาตไมค์สำหรับเซสชันนี้ก่อน','permission');return}
  if(voiceOn.current||micOpening.current)return
  micOpening.current=true
  const generation=life.current,epoch=micEpoch.current
  try{
   const stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true},video:false})
   if(!session.current||generation!==life.current||epoch!==micEpoch.current){stream.getTracks().forEach(t=>t.stop());micOpening.current=false;return}
   mic.current=stream;voiceOn.current=true
   const ctx=new AudioContext();audio.current=ctx;await ctx.resume();const analyser=ctx.createAnalyser();analyser.fftSize=1024;ctx.createMediaStreamSource(stream).connect(analyser);const buffer=new Float32Array(analyser.fftSize)
   const queue=new LatestVoiceQueue<Blob>(async blob=>{
    const controller=new AbortController();transcription.current=controller
    const timer=setTimeout(()=>controller.abort(),60000)
    try{const form=new FormData();form.append('file',blob,'voice.webm')
     const res=await fetch('/api/operator/transcribe',{method:'POST',headers:headers(),body:form,signal:controller.signal})
     const data=await res.json();if(!res.ok)throw Error(data.detail);return data.text||''
    }finally{clearTimeout(timer)}
   },value=>{if(value)void actions.current.command(value);else setState('Listening')},
   e=>{log(e instanceof Error?e.message:String(e),'voice error');setState('Listening')})
   voiceQueue.current=queue;micOpening.current=false
   let lastVoice=0,startTime=0
   const record=()=>{
    const revision=queue.invalidate()
    // Barge-in invalidates both model output and old transcription immediately.
    life.current++;request.current?.abort();speechSynthesis.cancel()
    setState('Listening')
    const r=new MediaRecorder(stream);recorder.current=r;const chunks:Blob[]=[];startTime=performance.now()
    r.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)}
    r.onstop=()=>{
     if(!voiceOn.current||!session.current||epoch!==micEpoch.current)return
     const blob=new Blob(chunks,{type:r.mimeType});if(blob.size<1000)return
     setState('Transcribing');queue.submit(blob,revision)
    }
    r.start()
   }
   setState('Listening');log('Listening — ไมค์ทำงานและถอดเสียงด้วย Whisper ในเครื่อง','voice')
   let ticks=0
   const sample=()=>{
    if(!voiceOn.current||epoch!==micEpoch.current)return
    analyser.getFloatTimeDomainData(buffer);const rms=Math.sqrt(buffer.reduce((sum,x)=>sum+x*x,0)/buffer.length);const now=performance.now();if(++ticks%4===0)setLevel(Math.min(1,rms*12))
    if(rms>0.035){lastVoice=now;if(speechSynthesis.speaking){speechSynthesis.cancel();setState('Listening')}if(recorder.current?.state!=='recording')record()}
    if(recorder.current?.state==='recording'&&(now-lastVoice>800||now-startTime>12000))recorder.current.stop()
    frames.current[0]=requestAnimationFrame(sample)
   }
   sample()
  }catch(e:any){stopMic();log(e.message,'microphone error')}
 }
 const switchCamera=async()=>{
  if(!grants.includes('camera')){log('ต้องอนุญาตกล้องสำหรับเซสชันนี้ก่อน','permission');return}
  if(camera.current)return
  try{
   const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:facing,width:640,height:480},audio:false})
   if(!session.current){stream.getTracks().forEach(t=>t.stop());return}
   camera.current=stream;setView('camera')
   if(video.current){video.current.srcObject=stream;await video.current.play()}
   log('Camera view — กำลังเปิด gesture_tracker ในเครื่อง','switch_view')
   const files=await FilesetResolver.forVisionTasks('/operator/wasm')
   const tracker=await GestureRecognizer.createFromOptions(files,{baseOptions:{modelAssetPath:'/operator/gesture_recognizer.task'},runningMode:'VIDEO',numHands:1})
   if(!camera.current){tracker.close();return}recognizer.current=tracker
   let last=0,palm=0,cooldown=0,previousX:number|null=null,previousTime=0,pinched=false,drag:{x:number,y:number}|null=null
   const track=()=>{
    const v=video.current,c=canvas.current
    if(!camera.current||!recognizer.current||!v||!c)return
    const now=performance.now()
    if(v.readyState>=2&&now-last>90){
     last=now;const detected=tracker.recognizeForVideo(v,now);const points=detected.landmarks[0],name=detected.gestures[0]?.[0]?.categoryName
     const context=c.getContext('2d')!;c.width=v.videoWidth;c.height=v.videoHeight;context.clearRect(0,0,c.width,c.height)
     if(points){
      context.fillStyle='#83ffe7';points.forEach(p=>{context.beginPath();context.arc((1-p.x)*c.width,p.y*c.height,4,0,Math.PI*2);context.fill()})
      const pinch=Math.hypot(points[4].x-points[8].x,points[4].y-points[8].y)<0.045
      if(name==='Open_Palm'){if(!palm)palm=now;if(now-palm>1000&&now>cooldown){setGesture('Open palm → Listening');actions.current.listen();cooldown=now+1800;palm=0}}else palm=0
      if(name==='Closed_Fist'&&now>cooldown){setGesture('Fist → Cancel');actions.current.cancel();cooldown=now+1800}
      const bounds=v.getBoundingClientRect(),scale=Math.max(bounds.width/v.videoWidth,bounds.height/v.videoHeight)
      const x=bounds.left+(1-points[8].x)*v.videoWidth*scale-(v.videoWidth*scale-bounds.width)/2,y=bounds.top+points[8].y*v.videoHeight*scale-(v.videoHeight*scale-bounds.height)/2
      if(pinch&&!pinched){const target=document.elementFromPoint(x,y)?.closest('[data-gesture]') as HTMLElement|null;if(target?.tagName==='BUTTON')target.click();else if(target?.classList.contains('operator-panel'))drag={x,y};setGesture('Pinch → Select / drag panel')}
      if(pinch&&drag){setOffset(dragUpdate(drag,{x,y}));drag={x,y}}if(!pinch)drag=null;pinched=pinch
      if(!pinch&&previousX!==null&&now-previousTime<300&&Math.abs(points[0].x-previousX)>0.2&&now>cooldown){const direction=points[0].x>previousX?-1:1;setPanel(panels[(panels.indexOf(panelRef.current)+direction+4)%4]);setGesture('Swipe → Switch panel');cooldown=now+1000}
      if(now-previousTime>200){previousX=points[0].x;previousTime=now}
     }else{palm=0;previousX=null;pinched=false;drag=null}
    }
    frames.current[1]=requestAnimationFrame(track)
   }
   track()
  }catch(e:any){log(e.message,'camera / gesture error');stopCamera()}
 }
 actions.current={command,listen,camera:switchCamera,cancel}
 const runQuick=(value:string)=>{if(!token){begin();return}void command(value)}
 const overview=[['◉','AI Core',online?(modelInfo?.current?.status||'Unknown'):'ตรวจสถานะไม่ได้'],['◎','Memory',token&&grants.includes('memory')?'อนุญาตการค้นหา':'ยังไม่อนุญาต'],['♩','Voice',voiceOn.current?'Mic active':'Mic off'],['◇','Workspace',panel],['⬡','Runtime',online?(modelInfo?.current?.backend||'Unknown'):'Unavailable'],['⌘','Session',token?'สิทธิ์ '+grants.length+' รายการ':'ยังไม่เริ่มเซสชัน']]
 return <main className={'operator '+view}>
  <header className="op-header"><div className="op-health"><i className={online?'live':''}/><span>SYSTEM STATUS <b>{online?'ONLINE':'UNAVAILABLE'}</b></span></div><div className="op-clock"><small>{now.toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'long',year:'numeric'})}</small><time>{now.toLocaleTimeString('en-GB')}</time></div><button className="op-session" onClick={()=>token?stop():begin()}>{token?'จบเซสชัน / ถอนสิทธิ์':'เริ่มเซสชัน'} <span>◎</span></button></header>
  <div className="op-title"><div><small>AIRIS UNIVERSAL AI</small><h1>Command Center</h1></div><span>OPERATOR MODE <i/> {state}</span></div>
  <div className="op-grid">
   <section className="op-card op-overview"><h2>AI CORE OVERVIEW</h2>{overview.map(([icon,title,value])=><div className="op-stat" key={title}><span className="op-icon">{icon}</span><div><b>{title}</b><small>{value}</small></div></div>)}</section>
   <section className="op-card op-hero">
    <div className="op-hero-top"><span>NEURAL INTERFACE</span><span>{view==='camera'?'CAMERA VIEW':'CORE VISUALIZATION'}</span></div>
    <video ref={video} muted playsInline className="operator-camera" style={{display:view==='camera'?'block':'none'}}/>
    <canvas ref={canvas} className="operator-hands" style={{display:view==='camera'?'block':'none'}}/>
    {view==='core'&&<OperatorCore state={state}/>}
    <div className="op-hero-bottom"><span><i className={voiceOn.current?'live':''}/>{voiceOn.current?'MIC ACTIVE':'MIC OFF'}</span><span>{token?'SESSION AUTHORIZED':'AWAITING PERMISSION'}</span></div>
   </section>
   <section className="op-card op-feed"><h2>LIVE ACTIVITY <span>{entries.length?'SESSION':'NO EVENTS'}</span></h2><div className="op-events">{entries.length?entries.slice(-5).reverse().map((e,i)=><article key={i}><small>{e.at} · {e.source}</small><p>{e.text}</p></article>):<div className="op-empty"><span>⌁</span><p>ยังไม่มีกิจกรรม</p><small>คำสั่งและผลลัพธ์จริงจะปรากฏที่นี่<br/>เมื่อเริ่มใช้งานเซสชัน</small></div>}</div></section>
   <section className="op-card op-workspaces"><h2>AGENT WORKSPACES <span>SELECT PANEL</span></h2><nav className="operator-panels">{panels.map((p,i)=><button data-gesture className={p===panel?'selected':''} key={p} onClick={()=>setPanel(p)}><span className="op-icon">{['⌘','⌕','☷','◎'][i]}</span><span>{p}<small>{p===panel?'Selected workspace':'Standby panel'}</small></span></button>)}</nav><small className="op-note">แผงจัดหมวดคำสั่ง ไม่ใช่เอเจนต์ที่รันแยกอยู่เบื้องหลัง</small></section>
   <section className="op-card op-quick"><h2>QUICK COMMANDS</h2><button data-gesture onClick={()=>runQuick('รายชื่อแอป')}>⌘ <span>แสดงแอปในเครื่อง</span> ↗</button><button data-gesture onClick={()=>{if(!token)begin();else if(voiceOn.current)stopMic();else void listen()}}>♩ <span>{voiceOn.current?'ปิดไมค์':'เริ่มฟังเสียง'}</span> ↗</button><button data-gesture onClick={()=>{if(!token)begin();else if(view==='camera')stopCamera();else void switchCamera()}}>◉ <span>{view==='camera'?'กลับ AI Core':'เปิดกล้อง / Gestures'}</span> ↗</button><button onClick={()=>{setText('ค้นเว็บ ');document.getElementById('operator-command')?.focus()}}>⌕ <span>ค้นเว็บพร้อมอ้างอิง</span> ↗</button></section>
   <section className="op-card op-monitor"><h2>SESSION MONITOR</h2><div className="op-meters">{[[online?String(systemInfo?.websocket_clients??'—'):'—','Chat clients'],[String(entries.filter(e=>e.source==='you').length),'Commands'],[token?String(grants.length):'0','Permissions']].map(([value,label])=><div key={label}><div className="op-ring">{value}</div><small>{label}</small></div>)}</div><small>ค่าจากเซิร์ฟเวอร์และเซสชันนี้ · ไม่มีข้อมูล CPU / RAM</small></section>
   <section className="op-card op-models"><h2>LOCAL MODEL <span>{online?'SERVER REPORTED':'OFFLINE'}</span></h2><div className="op-model-current"><span className="op-icon">⬡</span><div><b>{modelInfo?.current?.model||'รอข้อมูลจากเซิร์ฟเวอร์'}</b><small>{online?modelInfo?.current?.backend+' · '+modelInfo?.current?.status:'ตรวจสถานะล่าสุดไม่ได้'}</small></div></div><div className="op-model-list">{(modelInfo?.models||[]).filter((m:any)=>m.backend==='ollama').map((m:any)=><span key={m.id} title={m.description}>{m.name}<small>{m.installed?'พบในเครื่อง':'ยังไม่พบ / ตรวจสอบไม่ได้'}</small></span>)}</div><small>ใช้โมเดลในเครื่อง · ไม่เรียก API โมเดลแบบเสียเงิน</small></section>
   <section data-gesture className="op-card operator-panel" style={{transform:`translate(${offset.x}px,${offset.y}px)`}}><h2>{panel.toUpperCase()} / COMMAND OUTPUT <button onClick={()=>setOffset({x:0,y:0})}>จัดตำแหน่งใหม่</button></h2><div className="op-output">{!results.length&&!entries.length&&<p className="op-note">เริ่มเซสชันแล้วพิมพ์คำสั่ง หรือเปิดไมค์เพื่อสนทนากับ Airis</p>}{results.map((r,i)=><article key={i}><b>{r.title}</b><p>{r.content}</p>{r.url&&/^https?:\/\//.test(r.url)&&<a href={r.url} target="_blank" rel="noreferrer">เปิดแหล่งอ้างอิง ↗</a>}<small>{r.source} · {r.timestamp||'ไม่ระบุเวลา'}</small></article>)}<div className="operator-transcript" aria-live="polite">{entries.map((e,i)=><p key={i}><small>{e.at} · {e.source}</small>{e.text}</p>)}</div></div></section>
  </div>
  <div className="operator-controls"><button disabled={starting} onClick={forget}>เปลี่ยน / ลืมสิทธิ์ที่จำไว้</button><select aria-label="Camera facing" value={facing} disabled={view==='camera'} onChange={e=>setFacing(e.target.value)}><option value="user">กล้องหน้า</option><option value="environment">กล้องหลัง</option></select><p className="operator-feedback">{gesture||'Palm 1s → Listen · Pinch → Select / drag · Swipe → Panel · Fist → Cancel'}</p><button data-gesture onClick={cancel} disabled={!token}>หยุดคำตอบ / เสียง</button></div>
  <footer className="op-command-bar"><button className={'op-talk '+(voiceOn.current?'listening':'')} onClick={()=>{if(!token)begin();else if(voiceOn.current)stopMic();else void listen()}}><div className="operator-wave" aria-label="ระดับเสียงไมค์">{Array.from({length:16},(_,i)=><i key={i} style={{height:4+level*(12+18*Math.abs(Math.sin(i)))}}/>)}</div><span>TALK TO AIRIS<small>{voiceOn.current?'Listening enabled':'Tap to start'}</small></span></button><form onSubmit={e=>{e.preventDefault();if(!token){begin();return}if(text.trim()){void command(text);setText('')}}}><input id="operator-command" aria-label="Operator command" value={text} onChange={e=>setText(e.target.value)} placeholder="ค้นเว็บ … / เปิดแอป … / อ่านไฟล์ …"/><button>ส่งคำสั่ง ↗</button></form></footer>
  {!token&&permissionOpen&&<dialog ref={permissionDialog} className="op-permission-backdrop" onCancel={e=>{if(starting)e.preventDefault();else setPermissionOpen(false)}} aria-label="สิทธิ์เซสชัน Airis"><section className="operator-permissions"><button className="permission-close" disabled={starting} aria-label="ปิดหน้าสิทธิ์" onClick={()=>setPermissionOpen(false)}>×</button><small>SESSION PERMISSIONS</small><h2>เริ่มเซสชัน Airis</h2><p>จำความยินยอมครั้งเดียวสำหรับเว็บนี้ เปลี่ยน/ลืมสิทธิ์ได้ทุกเมื่อ ไมค์และกล้องต้องกดเปิดเอง และ action เสี่ยงสูงยังต้องยืนยัน</p>{[['voice','ไมค์และเสียงพูด'],['camera','กล้องและท่าทางมือ'],['files','เข้าถึงไฟล์ตามขอบเขตที่อนุญาต (ค่าเริ่มต้น: โฟลเดอร์ผู้ใช้)'],['web','ค้นอินเทอร์เน็ตพร้อมลิงก์อ้างอิง'],['memory','ค้นความจำ Airis'],['system','เปิดแอปที่ติดตั้งทั้งหมดตามสิทธิ์ macOS']].map(([id,label])=><label key={id}><input type="checkbox" checked={grants.includes(id)} onChange={e=>setGrants(g=>e.target.checked?[...g,id]:g.filter(x=>x!==id))}/>{label}</label>)}{grants.includes('files')&&<input aria-label="โฟลเดอร์ที่อนุญาต" value={root} onChange={e=>setRoot(e.target.value)} placeholder="เว้นว่าง = โฟลเดอร์ผู้ใช้ หรือ / = ทุกตำแหน่งที่ macOS อนุญาต"/>}{sessionError&&<p role="alert">{sessionError}</p>}<button disabled={starting} onClick={start}>{starting?'กำลังเริ่มเซสชัน…':'อนุญาตสิทธิ์ที่เลือกและเริ่ม'}</button></section></dialog>}
 </main>
}
