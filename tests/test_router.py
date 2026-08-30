from app.core.router import Router

def test_search_route():
    assert Router().route("What is the latest AI news?") == "search"

def test_normal_route():
    assert Router().route("Hello JARVIS") == "memory_llm"
