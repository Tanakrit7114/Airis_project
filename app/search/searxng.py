import requests
from app.config import SEARXNG_URL, ENABLE_SEARCH


class SearXNG:
    def search_results(self, query, limit=5):
        if not ENABLE_SEARCH:
            return []
        try:
            response = requests.get(
                f"{SEARXNG_URL}/search",
                params={
                    "q": query,
                    "format": "json",
                    "categories": "general",
                },
                headers={"Accept":"application/json","User-Agent":"Airis/1.0 local research client"},
                timeout=10,
            )
            if getattr(response, "status_code", 200) in {401,403}:
                # Some local SearXNG installations disable JSON/HTML output.
                # Use the public metadata provider instead of surfacing the
                # local gateway error to the chat UI.
                from app.search.public_web import search_web
                return search_web(query, limit)
            response.raise_for_status()
            data = response.json()
            results = []
            for item in data.get("results", [])[:limit]:
                results.append({
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "url": item.get("url", ""),
                    "engine": item.get("engine", ""),
                    "score": item.get("score", 0.0) or 0.0,
                })
            if results:return results
            from app.search.public_web import search_web
            return search_web(query,limit)
        except requests.RequestException as e:
            print("[SearXNG ERROR]", repr(e))
            if getattr(e, "response", None) is not None:
                print("[SearXNG STATUS]", e.response.status_code)
                print("[SearXNG BODY]", e.response.text[:1000])
            try:
                from app.search.public_web import search_web
                return search_web(query,limit)
            except Exception:
                return []

    def search(self, query, limit=5):
        results = self.search_results(query, limit=limit)
        return "\n".join(
            f"- {r['title']}\n  {r['content']}\n  {r['url']}" for r in results
        )
