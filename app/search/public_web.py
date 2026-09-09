"""Public search metadata with original source URLs; no invented citations."""
from datetime import datetime, timezone
from urllib.parse import urlparse

def search_web(query, limit=6):
    from ddgs import DDGS
    results=DDGS(timeout=12).text(query,max_results=limit)
    seen=set();out=[]
    for item in results:
        url=item.get("href",item.get("url",""))
        if urlparse(url).scheme not in {"http","https"} or url in seen:continue
        seen.add(url)
        out.append({"title":item.get("title",url),"url":url,"source":url,
                    "content":item.get("body",""),"timestamp":datetime.now(timezone.utc).isoformat(),
                    "engine":"public web search","evidence":"search snippet; timestamp is retrieval time"})
    return out
