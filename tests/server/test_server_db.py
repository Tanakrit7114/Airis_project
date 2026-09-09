from app.server.db import DashboardDB


def test_session_and_message(tmp_path):
    db = DashboardDB(str(tmp_path / "jarvis.db"))
    session = db.create_session("Test")
    assert session["title"] == "Test"
    db.add_message(session["id"], "user", "hello", source="memory/general", route="memory_llm")
    db.add_message(session["id"], "assistant", "hi", source="memory/general", route="memory_llm")
    messages = db.list_messages(session["id"])
    assert len(messages) == 2
    assert messages[0]["content"] == "hello"
