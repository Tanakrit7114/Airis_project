from app.search.manager import SearchManager
from app.search.providers.searxng_provider import SearXNGProvider


def test_search_manager():

    manager = SearchManager(
        providers=[
            SearXNGProvider(),
        ]
    )

    response = manager.search(
        "Python programming",
        limit=5,
    )

    assert response.query == "Python programming"
    assert isinstance(response.results, list)
