import React,{useState} from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import hljs from 'highlight.js/lib/common'
import 'highlight.js/styles/github-dark.css'
import '../artifacts.css'

export default function MarkdownContent({content}:{content:string}){
 return <div className="markdown-body"><ReactMarkdown remarkPlugins={[remarkGfm,remarkMath]} rehypePlugins={[rehypeKatex]} components={{
  a:({href,children})=><a href={href} target="_blank" rel="noreferrer">{children}</a>,
  pre:({children})=>{const child=React.Children.toArray(children)[0];if(React.isValidElement(child)){const props=child.props as {className?:string;children?:React.ReactNode};return <CodeBlock className={props.className} code={String(props.children??'').replace(/\n$/,'')}/>};return <pre>{children}</pre>},
  code:({children,className})=><code className={className||'inline-code'}>{children}</code>,
  table:({children})=><div className="table-scroll"><table>{children}</table></div>
 }}>{content||''}</ReactMarkdown></div>
}
function CodeBlock({className,code}:{className?:string;code:string}){
 const [notice,setNotice]=useState(''),[preview,setPreview]=useState<string|null>(null)
 const lang=className?.replace('language-','')||'text'
 const isHtml=/^(html|htm)$/i.test(lang)||/^\s*(<!doctype html|<html[\s>])/i.test(code)
 const highlighted=hljs.getLanguage(lang)?hljs.highlight(code,{language:lang}).value:null
 const copy=async()=>{try{if(navigator.clipboard&&window.isSecureContext)await navigator.clipboard.writeText(code);else{const field=document.createElement('textarea');field.value=code;field.style.position='fixed';field.style.opacity='0';document.body.append(field);try{field.select();if(!document.execCommand('copy'))throw Error()}finally{field.remove()}}setNotice('คัดลอกแล้ว')}catch{setNotice('คัดลอกไม่ได้ กรุณาเลือกโค้ดแล้วกด Ctrl/Cmd+C')}}
 const download=()=>{const url=URL.createObjectURL(new Blob([code],{type:isHtml?'text/html;charset=utf-8':'text/plain;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=isHtml?'airis-website.html':'airis-code.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
 const show=()=>{const doc=new DOMParser().parseFromString(code,'text/html');const policy=doc.createElement('meta');policy.httpEquiv='Content-Security-Policy';policy.content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; connect-src 'none'; form-action 'none'; frame-src 'none'; base-uri 'none'";doc.head.prepend(policy);setPreview('<!doctype html>'+doc.documentElement.outerHTML)}
 return <div className="code-shell"><div className="airis-code-toolbar"><span>{lang}</span><button onClick={copy}>คัดลอกโค้ด</button><button onClick={download}>{isHtml?'ดาวน์โหลด HTML':'ดาวน์โหลดโค้ด'}</button>{isHtml&&<button onClick={show}>เปิด / อัปเดตตัวอย่าง</button>}<span role="status">{notice}</span></div><pre className="code-block">{highlighted?<code dangerouslySetInnerHTML={{__html:highlighted}}/>:<code>{code}</code>}</pre>{preview!==null&&<section className="airis-preview"><button onClick={()=>setPreview(null)}>ปิดตัวอย่าง</button><iframe title="ตัวอย่างเว็บไซต์ HTML" sandbox="allow-scripts" referrerPolicy="no-referrer" srcDoc={preview}/></section>}</div>
}
