from app.core.router import Router


def test_search_route():
    assert Router().route(
        "What is the latest AI news?"
    ) == "search"


def test_normal_route():
    assert Router().route(
        "Hello JARVIS"
    ) == "memory_llm"


def test_system_date_route():
    assert Router().route(
        "today is?"
    ) == "tool:system"


def test_system_time_route():
    assert Router().route(
        "what time is it?"
    ) == "tool:system"


def test_system_current_date_route():
    assert Router().route(
        "what is the current date?"
    ) == "tool:system"


def test_calculator_route():
    assert Router().route(
        "calculate 123 + 456"
    ) == "tool:calculator"
