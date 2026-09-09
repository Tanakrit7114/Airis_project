from __future__ import annotations
import re
from typing import Any

WRITE_ACTIONS = {
    "gmail_send", "drive_create_file", "calendar_create_event", "github_create_issue", "notion_update_page", "slack_send_message"
}

def normalize_write_query(tool: str, query: str) -> str:
    t=query.strip()
    if tool == "gmail_send" and "|" not in t:
        import re
        email_match=re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", t)
        subj_match=re.search(r"(?:subject|หัวข้อ)\s*[:：-]?\s*(.+?)(?:\s+(?:body|เนื้อหา)\s*[:：-]?\s+|$)", t, re.I)
        body_match=re.search(r"(?:body|เนื้อหา)\s*[:：-]?\s*(.+)$", t, re.I)
        if email_match and subj_match:
            return f"{email_match.group(0)} | {subj_match.group(1).strip()} | {(body_match.group(1).strip() if body_match else '')}"
    return t


class ExtensionToolManager:
    def __init__(self, extension_manager): self.manager=extension_manager
    def _call(self, ext, action, query="", **kwargs): return self.manager.action(ext, action, query=query, **kwargs)
    def execute(self, name: str, query: str = "", **kwargs) -> Any:
        mapping={
            "gmail_search":("gmail","search"), "gmail_read":("gmail","read"), "gmail_send":("gmail","send"),
            "drive_search":("drive","search"), "drive_read_file":("drive","read"), "drive_create_file":("drive","create"),
            "calendar_list_events":("calendar","upcoming"), "calendar_create_event":("calendar","create"),
            "github_list_repos":("github","repos"), "github_read_file":("github","read"), "github_create_issue":("github","issue"),
            "notion_search":("notion","search"), "notion_read_page":("notion","read"), "notion_update_page":("notion","update"),
            "slack_list_channels":("slack","channels"), "slack_read_messages":("slack","history"), "slack_send_message":("slack","send"),
        }
        if name not in mapping: raise RuntimeError(f"Unknown extension tool: {name}")
        ext, action=mapping[name]; return self._call(ext, action, normalize_write_query(name, query), **kwargs)

def detect_extension_intent(text: str) -> dict[str, Any] | None:
    t=text.lower()
    service=None
    for key, aliases in {
        "gmail":["gmail","อีเมล","อีเมล์","email","mail"], "drive":["google drive","drive","ไฟล์บนไดรฟ์"],
        "calendar":["calendar","ปฏิทิน","ตารางนัด","ตารางกิจกรรม"], "github":["github","repo","repository"],
        "notion":["notion","page ใน notion"], "slack":["slack","channel","แชนแนล"],
    }.items():
        if any(a in t for a in aliases): service=key; break
    if not service: return None
    write=any(k in t for k in ["send","ส่ง","สร้าง","เพิ่ม","create","update","แก้ไข","เปลี่ยน","issue","ข้อความ"])
    if service=="gmail": name="gmail_send" if write and any(k in t for k in ["ส่ง","send"]) else ("gmail_read" if any(k in t for k in ["อ่าน","read"]) else "gmail_search")
    elif service=="drive": name="drive_create_file" if write and any(k in t for k in ["สร้าง","create"]) else ("drive_read_file" if any(k in t for k in ["อ่าน","เปิด","read"]) else "drive_search")
    elif service=="calendar": name="calendar_create_event" if write else "calendar_list_events"
    elif service=="github": name="github_create_issue" if write and "issue" in t else ("github_read_file" if any(k in t for k in ["อ่านไฟล์","read file"]) else "github_list_repos")
    elif service=="notion": name="notion_update_page" if write else ("notion_read_page" if any(k in t for k in ["อ่าน","เปิด"]) else "notion_search")
    else: name="slack_send_message" if write and any(k in t for k in ["ส่ง","send"]) else ("slack_read_messages" if any(k in t for k in ["ข้อความ","message","อ่าน"]) else "slack_list_channels")
    return {"tool":name,"write":name in WRITE_ACTIONS,"service":service}

def tool_description_text() -> str:
    return "Available extensions: Gmail search/read/send; Drive search/read/create; Calendar list/create; GitHub list/read/create issue; Notion search/read/update; Slack list/read/send. Use only connected extensions. Write actions require user confirmation."
