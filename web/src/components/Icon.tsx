import React from 'react'
type P={name:string;size?:number}
const paths:Record<string,React.ReactNode>={
 message:<><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/><path d="M8 9h8M8 13h5"/></>,
 dashboard:<><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
 plug:<><path d="M12 2v6M12 16v6M5 8h14v4a7 7 0 0 1-14 0z"/></>,
 zap:<><path d="m13 2-9 12h7l-1 8 9-12h-7z"/></>,
 plus:<><path d="M12 5v14M5 12h14"/></>,
 paperclip:<path d="m21 11-8.5 8.5a5 5 0 0 1-7-7L14 4a3.5 3.5 0 1 1 5 5l-8.5 8.5a2 2 0 1 1-3-3L15 7"/>,
 send:<><path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/></>,
 chevron:<path d="m6 9 6 6 6-6"/>,
 loader:<><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></>,
 bot:<><rect x="4" y="7" width="16" height="12" rx="3"/><path d="M8 11h.01M16 11h.01M9 15h6M12 7V3"/></>,
 user:<><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>,
 copy:<><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></>,
 check:<path d="m5 12 4 4L19 6"/>,
 external:<><path d="M14 3h7v7M10 14 21 3"/><path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5"/></>,
 mail:<><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></>,
 folder:<><path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></>,
 calendar:<><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></>,
 github:<><path d="M12 2a10 10 0 0 0-3 19.53c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.18-3.37-1.18-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.52 1.03 1.52 1.03.9 1.53 2.36 1.09 2.94.83.09-.65.35-1.09.63-1.34-2.22-.26-4.56-1.11-4.56-4.95 0-1.09.39-1.98 1.03-2.68-.1-.26-.45-1.35.1-2.66 0 0 .84-.27 2.75 1.02A9.6 9.6 0 0 1 12 7.84c.85 0 1.71.11 2.51.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.31.2 2.4.1 2.66.64.7 1.03 1.59 1.03 2.68 0 3.85-2.34 4.69-4.57 4.94.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2z"/></>,
 file:<><path d="M6 2h8l4 4v16H6z"/><path d="M14 2v5h5"/></>,
 chat:<><path d="M4 5h16v12H8l-4 4z"/></>,
}
export default function Icon({name,size=16}:P){return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]||paths.chat}</svg>}
