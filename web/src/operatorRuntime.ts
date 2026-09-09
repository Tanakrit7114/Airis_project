export type Point = {x:number;y:number}
// Snapshot the delta now; React may run the updater after tracking moves on.
export function dragUpdate(previous:Point, next:Point) {
 const dx=next.x-previous.x,dy=next.y-previous.y
 return (offset:Point)=>({x:offset.x+dx,y:offset.y+dy})
}

// One transcription in flight, one pending utterance. Recording never waits
// for transcription or model generation; superseded results cannot execute.
export class LatestVoiceQueue<T> {
 private revision=0
 private pending:{value:T;revision:number}|null=null
 private busy=false
 private closed=false
 constructor(private transcribe:(value:T)=>Promise<string>,private accept:(text:string)=>void,private error:(e:unknown)=>void){}
 invalidate(){this.pending=null;return ++this.revision}
 submit(value:T,revision:number){
  if(this.closed||revision!==this.revision)return
  this.pending={value,revision};void this.drain()
 }
 close(){this.closed=true;this.invalidate()}
 private async drain(){
  if(this.busy)return
  this.busy=true
  try{while(this.pending&&!this.closed){
   const item=this.pending;this.pending=null
   try{const text=await this.transcribe(item.value);if(!this.closed&&item.revision===this.revision)this.accept(text)}
   catch(e){if(!this.closed&&item.revision===this.revision)this.error(e)}
  }}finally{this.busy=false}
 }
}
