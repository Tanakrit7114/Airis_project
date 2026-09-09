import requests
from app.config import SEARXNG_URL, ENABLE_SEARCH

class SearXNG:
    def search(self, query, limit=5):
        if not ENABLE_SEARCH:
            return ""

        try:
            response = requests.get(
                f"{SEARXNG_URL}/search",
                params={
                    "q": query,
                    "format": "json",
                    "categories": "general",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", [])[:limit]:
                title = item.get("title", "")
                content = item.get("content", "")
                url = item.get("url", "")
                results.append(
                    f"- {title}\n  {content}\n  {url}"
                )

            return "\n".join(results)

        except requests.RequestException as e:
            print("[SearXNG ERROR]", repr(e))
            if hasattr(e, "response") and e.response is not None:
                print("[SearXNG STATUS]", e.response.status_code)
                print("[SearXNG BODY]", e.response.text[:1000])
            return ""
