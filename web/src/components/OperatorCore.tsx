import React from 'react'

export default function OperatorCore({state}:{state:string}){
 return <div className={'operator-core '+state.toLowerCase()}>
  <svg viewBox="0 0 640 390" aria-hidden="true">
   <defs><radialGradient id="coreGlow"><stop stopColor="#08bed1" stopOpacity=".22"/><stop offset="1" stopColor="#071727" stopOpacity="0"/></radialGradient><filter id="coreBlur"><feGaussianBlur stdDeviation="3"/></filter></defs>
   <ellipse cx="320" cy="200" rx="280" ry="185" fill="url(#coreGlow)"/>
   <g fill="none" stroke="#26a8cc" strokeWidth=".65" opacity=".38">
    {Array.from({length:11},(_,i)=><ellipse key={'lat'+i} cx="320" cy={65+i*25} rx={Math.sqrt(Math.max(0,1-((i-5)/5.5)**2))*140} ry="19"/>)}
    {Array.from({length:9},(_,i)=><ellipse key={'lng'+i} cx="320" cy="190" rx={18+i*15} ry="145" transform={'rotate('+(i%2?12:-12)+' 320 190)'}/>)}
    <circle cx="320" cy="190" r="145" strokeWidth="2"/>
    {[-28,0,28].map(angle=><ellipse key={angle} cx="320" cy="194" rx="258" ry="51" transform={'rotate('+angle+' 320 194)'} stroke="#4dddeb"/>)}
    {Array.from({length:9},(_,i)=><ellipse key={'floor'+i} cx="320" cy="337" rx={60+i*20} ry={5+i*3} opacity={1-i*.08}/>)}
   </g>
   <g className="core-orbit"><circle cx="90" cy="175" r="6" fill="#8cf7ff" filter="url(#coreBlur)"/><circle cx="90" cy="175" r="2" fill="white"/><circle cx="548" cy="219" r="6" fill="#8cf7ff" filter="url(#coreBlur)"/></g>
   <g fill="#50d9eb" opacity=".5">{Array.from({length:38},(_,i)=><circle key={i} cx={30+(i*137)%590} cy={25+(i*79)%340} r={i%5===0?1.7:.8}/>)}</g>
  </svg>
  <div className="core-label"><b>AIRIS</b><span>UNIVERSAL AI CORE</span><small>{state.toUpperCase()} · LOCAL FIRST</small></div>
 </div>
}
