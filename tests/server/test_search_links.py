from app.search.searxng import SearXNG


def test_search_results_returns_structured_links(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {"results": [{"title": "KKU", "content": "Khon Kaen University", "url": "https://www.kku.ac.th"}]}

    monkeypatch.setattr("app.search.searxng.requests.get", lambda *a, **k: Response())
    results = SearXNG().search_results("KKU")
    assert results[0]["url"] == "https://www.kku.ac.th"
    assert results[0]["title"] == "KKU"
