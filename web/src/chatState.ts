export function hydrateMessage(message:any){
 const meta=message.metadata||{}
 return {...message,done:true,sources:meta.sources||[],persistent_documents:meta.persistent_documents||[],
  extensionResult:meta.extension_result,image:meta.image?.url, imageMeta:meta.image,
  attachment:meta.attachment_filename, error:meta.error}
}

// Every response updates its own placeholder, never an unrelated last message.
export function updateResponse(messages:any[],id:string,event:any){
 return messages.map(message=>{
  if(message.id!==id)return message
  if(event.type==='token')return {...message,content:message.content+(event.text||'')}
  if(event.type==='image')return {...message,image:event.url,imageMeta:event,source:'image'}
  if(event.type==='extension_result')return {...message,extensionResult:{kind:event.kind,items:event.items}}
  if(event.type==='error')return {...message,done:true,error:true,content:[message.content,event.message||'เกิดข้อผิดพลาด กรุณาลองอีกครั้ง'].filter(Boolean).join('\n\n')}
  if(event.type==='done')return {...message,done:true,content:event.answer??message.content,
   source:event.source,sources:event.sources||[],persistent_documents:event.persistent_documents||[],
   extensionResult:event.extension_result||message.extensionResult,
   image:event.image?.url||message.image,imageMeta:event.image||message.imageMeta}
  return message
 })
}
