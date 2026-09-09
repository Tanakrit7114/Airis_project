from app.tools.system import system_tool, get_system_info


def test_system_info():
    info = get_system_info()

    assert "date" in info
    assert "time" in info
    assert "datetime" in info
    assert "weekday" in info


def test_date_query():
    result = system_tool("today is?")
    assert "Today is" in result


def test_time_query():
    result = system_tool("what time is it?")
    assert "current time" in result


def test_thai_date_query():
    result = system_tool("วันนี้วันอะไร")
    assert "Today is" in result


def test_thai_time_query():
    result = system_tool("ตอนนี้กี่โมง")
    assert "current time" in result
