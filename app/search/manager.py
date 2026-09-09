from app.search.models import SearchResponse
from app.search.providers.base import SearchProvider


class SearchManager:

    def __init__(
        self,
        providers: list[SearchProvider],
    ):
        self.providers = providers

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> SearchResponse:

        for provider in self.providers:

            try:

                print(
                    f"[SEARCH] Trying provider: "
                    f"{provider.name}"
                )

                response = provider.search(
                    query,
                    limit=limit,
                )

                if response.results:

                    print(
                        f"[SEARCH] "
                        f"{provider.name} returned "
                        f"{len(response.results)} results"
                    )

                    return response

                print(
                    f"[SEARCH] "
                    f"{provider.name} returned 0 results"
                )

            except Exception as exc:

                print(
                    f"[SEARCH PROVIDER ERROR] "
                    f"{provider.name}: {exc}"
                )

        return SearchResponse(
            query=query,
            results=[],
            provider=None,
        )
