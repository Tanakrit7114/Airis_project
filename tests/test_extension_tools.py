from app.tools.extensions_tools import detect_extension_intent

def test_extension_read_intents():
    assert detect_extension_intent("เช็คอีเมลใหม่จาก Gmail")["tool"] == "gmail_search"
    assert detect_extension_intent("ดู repository ใน GitHub")["tool"] == "github_list_repos"

def test_extension_write_intent():
    intent = detect_extension_intent("ส่งอีเมลจาก Gmail")
    assert intent["tool"] == "gmail_send"
    assert intent["write"] is True
