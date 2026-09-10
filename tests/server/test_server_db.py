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

def test_first_user_message_auto_titles_new_conversation(tmp_path):
    db = DashboardDB(str(tmp_path / "titles.db"))
    session = db.create_session()
    db.add_message(session["id"], "user", "  วางแผนอ่านสอบ   วิชา   Python  ", source="general", route="memory_llm")
    assert db.get_session(session["id"])["title"] == "วางแผนอ่านสอบ วิชา Python"

def test_explicit_title_is_preserved(tmp_path):
    db = DashboardDB(str(tmp_path / "titles.db"))
    session = db.create_session("My title")
    db.add_message(session["id"], "user", "ไม่ควรแทนที่ชื่อเอง", source="general", route="memory_llm")
    assert db.get_session(session["id"])["title"] == "My title"
