from app.search.models import SearchResponse, SearchResult
from app.search.providers.base import SearchProvider
from app.search.searxng import SearXNG


class SearXNGProvider(SearchProvider):

    @property
    def name(self) -> str:
        return "searxng"

    def __init__(self):
        self.client = SearXNG()

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> SearchResponse:

        raw = self.client.search(
            query,
            limit=limit,
        )

        results = []

        if not raw:
            return SearchResponse(
                query=query,
                results=[],
                provider=self.name,
            )

        blocks = raw.split("\n- ")

        for block in blocks:
            block = block.strip()

            if not block:
                continue

            lines = block.splitlines()

            title = lines[0].strip() if lines else ""
            content = lines[1].strip() if len(lines) > 1 else ""
            url = lines[2].strip() if len(lines) > 2 else ""

            results.append(
                SearchResult(
                    title=title,
                    content=content,
                    url=url,
                    engine=self.name,
                )
            )

        return SearchResponse(
            query=query,
            results=results[:limit],
            provider=self.name,
        )
