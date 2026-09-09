import requests

from app.search.models import SearchResponse, SearchResult
from app.search.providers.base import SearchProvider


class WebProvider(SearchProvider):

    @property
    def name(self) -> str:
        return "web"

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> SearchResponse:

        try:
            response = requests.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                },
                timeout=10,
            )

            response.raise_for_status()

            data = response.json()

            results = []

            abstract = data.get("AbstractText", "")
            abstract_url = data.get("AbstractURL", "")
            heading = data.get("Heading", "")

            if abstract:
                results.append(
                    SearchResult(
                        title=heading or query,
                        url=abstract_url,
                        content=abstract,
                        engine=self.name,
                    )
                )

            for topic in data.get("RelatedTopics", []):
                if not isinstance(topic, dict):
                    continue

                text = topic.get("Text", "")
                url = topic.get("FirstURL", "")

                if not text or not url:
                    continue

                results.append(
                    SearchResult(
                        title=text[:120],
                        url=url,
                        content=text,
                        engine=self.name,
                    )
                )

                if len(results) >= limit:
                    break

            return SearchResponse(
                query=query,
                results=results[:limit],
                provider=self.name,
            )

        except requests.RequestException as exc:
            print(f"[WEB SEARCH ERROR] {exc}")

            return SearchResponse(
                query=query,
                results=[],
                provider=self.name,
            )
