from __future__ import annotations

import json
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from app.config import MEMORY_DB


@dataclass(frozen=True)
class ExtensionDefinition:
    id: str
    name: str
    category: str
    description: str
    icon: str
    provider: str
    scopes: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()


EXTENSIONS = (
    ExtensionDefinition(
        "gmail", "Gmail", "Google", "Read and search email", "✉", "google",
        ("https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"),
        ("Read recent email", "Search email"),
    ),
    ExtensionDefinition(
        "drive", "Google Drive", "Google", "Search and read Drive files", "△", "google",
        ("https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/drive.file"),
        ("Search files", "Read metadata"),
    ),
    ExtensionDefinition(
        "calendar", "Google Calendar", "Google", "View appointments and events", "31", "google",
        ("https://www.googleapis.com/auth/calendar.readonly", "https://www.googleapis.com/auth/calendar.events"),
        ("View upcoming events",),
    ),
    ExtensionDefinition(
        "github", "GitHub", "Developer", "Read repositories and account data", "●", "github",
        ("read:user", "user:email", "repo"),
        ("View repositories", "View profile"),
    ),
    ExtensionDefinition(
        "notion", "Notion", "Workspace", "Search and read pages shared with this connection", "N", "notion",
        ("read_content", "update_content"),
        ("Search pages", "Read pages", "Edit pages"),
    ),
)

EXT_BY_ID = {e.id: e for e in EXTENSIONS}


class ExtensionManager:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.getenv("EXTENSIONS_DB", "data/extensions.db")
        self._memory_con = None
        if self.db_path != ":memory:":
            path = Path(self.db_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                path.touch(mode=0o600, exist_ok=True)
                os.chmod(path, 0o600)
            except OSError:
                pass
        else:
            self._memory_con = sqlite3.connect(":memory:", timeout=30, check_same_thread=False)
            self._memory_con.row_factory = sqlite3.Row
        self._init_db()

    def _connect(self):
        if self._memory_con is not None:
            return self._memory_con
        con = sqlite3.connect(self.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self):
        with self._connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS extension_tokens (
                    extension_id TEXT PRIMARY KEY,
                    token_json TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS extension_oauth_states (
                    state TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    extension_id TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            con.commit()

    def _get_token(self, extension_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute("SELECT token_json FROM extension_tokens WHERE extension_id=?", (extension_id,)).fetchone()
        if not row:
            return None
        try:
            return json.loads(row["token_json"])
        except Exception:
            return None

    def _save_token(self, extension_id: str, token: dict[str, Any]):
        with self._connect() as con:
            con.execute(
                "INSERT INTO extension_tokens(extension_id, token_json, updated_at) VALUES(?,?,?) "
                "ON CONFLICT(extension_id) DO UPDATE SET token_json=excluded.token_json, updated_at=excluded.updated_at",
                (extension_id, json.dumps(token, ensure_ascii=False), time.time()),
            )
            con.commit()

    def disconnect(self, extension_id: str):
        with self._connect() as con:
            con.execute("DELETE FROM extension_tokens WHERE extension_id=?", (extension_id,))
            con.commit()

    def list_extensions(self) -> list[dict[str, Any]]:
        return [{
            "id": e.id,
            "name": e.name,
            "category": e.category,
            "description": e.description,
            "icon": e.icon,
            "connected": self._get_token(e.id) is not None,
            "capabilities": list(e.capabilities),
        } for e in EXTENSIONS]

    def _credentials(self, provider: str) -> tuple[str | None, str | None]:
        if provider == "google":
            return os.getenv("GOOGLE_CLIENT_ID"), os.getenv("GOOGLE_CLIENT_SECRET")
        if provider == "github":
            return os.getenv("GITHUB_CLIENT_ID"), os.getenv("GITHUB_CLIENT_SECRET")
        if provider == "notion":
            return os.getenv("NOTION_CLIENT_ID"), os.getenv("NOTION_CLIENT_SECRET")
        return None, None

    def _redirect_uri(self, provider: str) -> str:
        base = os.getenv("JARVIS_PUBLIC_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
        return f"{base}/api/extensions/oauth/{provider}/callback"

    def connect_url(self, extension_id: str) -> str:
        ext = EXT_BY_ID[extension_id]
        client_id, client_secret = self._credentials(ext.provider)
        if not client_id or not client_secret:
            raise RuntimeError(f"ยังไม่ได้ตั้งค่า credentials สำหรับ {ext.name}")
        state = secrets.token_urlsafe(32)
        with self._connect() as con:
            con.execute(
                "INSERT INTO extension_oauth_states(state, provider, extension_id, created_at) VALUES(?,?,?,?)",
                (state, ext.provider, ext.id, time.time()),
            )
            con.commit()
        if ext.provider == "google":
            scopes = list(ext.scopes)
            params = {
                "client_id": client_id,
                "redirect_uri": self._redirect_uri("google"),
                "response_type": "code",
                "access_type": "offline",
                "prompt": "consent",
                "scope": " ".join(scopes),
                "state": state,
            }
            return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        if ext.provider == "github":
            # Keep the authorization request aligned with the scopes checked
            # by _request and used by the GitHub actions.
            params = {"client_id": client_id, "redirect_uri": self._redirect_uri("github"), "scope": " ".join(ext.scopes), "state": state}
            return "https://github.com/login/oauth/authorize?" + urlencode(params)
        if ext.provider == "notion":
            params = {"owner": "user", "client_id": client_id, "redirect_uri": self._redirect_uri("notion"), "response_type": "code", "state": state}
            return "https://api.notion.com/v1/oauth/authorize?" + urlencode(params)
        raise RuntimeError("Unknown provider")

    def handle_callback(self, provider: str, code: str, state: str):
        with self._connect() as con:
            row = con.execute("SELECT extension_id, created_at FROM extension_oauth_states WHERE state=? AND provider=?", (state, provider)).fetchone()
            if not row or time.time() - float(row["created_at"]) > 600:
                if row:
                    con.execute("DELETE FROM extension_oauth_states WHERE state=?", (state,))
                    con.commit()
                raise RuntimeError("OAuth state ไม่ถูกต้องหรือหมดอายุ")
            extension_id = row["extension_id"]
            con.execute("DELETE FROM extension_oauth_states WHERE state=?", (state,))
            con.commit()
        client_id, client_secret = self._credentials(provider)
        redirect_uri = self._redirect_uri(provider)
        if provider == "google":
            resp = requests.post("https://oauth2.googleapis.com/token", data={"code": code, "client_id": client_id, "client_secret": client_secret, "redirect_uri": redirect_uri, "grant_type": "authorization_code"}, timeout=30)
        elif provider == "github":
            resp = requests.post("https://github.com/login/oauth/access_token", data={"code": code, "client_id": client_id, "client_secret": client_secret, "redirect_uri": redirect_uri, "state": state}, headers={"Accept": "application/json"}, timeout=30)
        elif provider == "notion":
            resp = requests.post("https://api.notion.com/v1/oauth/token", json={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri}, auth=(client_id, client_secret), timeout=30)
        else:
            raise RuntimeError("Unknown provider")
        resp.raise_for_status()
        token = resp.json()
        if token.get("ok") is False:
            raise RuntimeError(token.get("error", "OAuth failed"))
        token["obtained_at"] = int(time.time())
        self._save_token(extension_id, token)
        return extension_id

    def _google_refresh(self, token: dict[str, Any]) -> dict[str, Any]:
        expires_at = token.get("obtained_at", 0) + int(token.get("expires_in", 0))
        if expires_at and time.time() < expires_at - 60:
            return token
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            return token
        client_id, client_secret = self._credentials("google")
        resp = requests.post("https://oauth2.googleapis.com/token", data={"client_id": client_id, "client_secret": client_secret, "refresh_token": refresh_token, "grant_type": "refresh_token"}, timeout=30)
        resp.raise_for_status()
        fresh = resp.json()
        fresh["refresh_token"] = refresh_token
        fresh["obtained_at"] = int(time.time())
        return fresh

    def _request(self, extension_id: str, method: str, url: str, **kwargs):
        token = self._get_token(extension_id)
        if not token:
            raise RuntimeError("ยังไม่ได้เชื่อมต่อ extension นี้")
        ext = EXT_BY_ID[extension_id]
        granted = token.get("scope", "")
        if isinstance(granted, str) and granted:
            granted_set = set(granted.replace(",", " ").split())
            required_set = set(ext.scopes)
            if required_set and not required_set.issubset(granted_set):
                raise RuntimeError(f"สิทธิ์ของ {ext.name} ไม่ครบ กรุณากด Connect ใหม่เพื่ออนุญาต scope ที่ต้องใช้")
        if ext.provider == "google":
            token = self._google_refresh(token)
            self._save_token(extension_id, token)
        access_token = token.get("access_token")
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {access_token}"
        resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
        if resp.status_code == 401 and ext.provider == "google":
            token = self._google_refresh(token)
            self._save_token(extension_id, token)
            headers["Authorization"] = f"Bearer {token.get('access_token')}"
            resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
        if resp.status_code == 401:
            # Do not advertise a stale token as connected. The next attempt
            # must go through OAuth again instead of repeatedly returning 401.
            self.disconnect(extension_id)
        resp.raise_for_status()
        return resp.json()

    def _access_token(self, extension_id: str) -> str:
        token = self._get_token(extension_id)
        if not token:
            raise RuntimeError("ยังไม่ได้เชื่อมต่อ extension นี้")
        ext = EXT_BY_ID[extension_id]
        if ext.provider == "google":
            token = self._google_refresh(token)
            self._save_token(extension_id, token)
        access_token = token.get("access_token")
        if not access_token:
            raise RuntimeError("Extension token ไม่มี access token")
        return access_token

    def test(self, extension_id: str) -> dict[str, Any]:
        ext = EXT_BY_ID[extension_id]
        if ext.provider == "google":
            info = self._request(extension_id, "GET", "https://www.googleapis.com/oauth2/v3/userinfo")
            return {"ok": True, "account": info.get("email") or info.get("name")}
        if ext.provider == "github":
            info = self._request(extension_id, "GET", "https://api.github.com/user")
            return {"ok": True, "account": info.get("login")}
        if ext.provider == "notion":
            info = self._request(extension_id, "GET", "https://api.notion.com/v1/users/me", headers={"Notion-Version": os.getenv("NOTION_VERSION", "2026-03-11")})
            return {"ok": True, "account": (info.get("name") or "Notion connection")}
        return {"ok": False}

    def action(self, extension_id: str, action: str, query: str = "") -> dict[str, Any]:
        if extension_id == "gmail" and action in {"recent", "search"}:
            params = {"maxResults": 10}
            if query:
                params["q"] = query
            data = self._request(extension_id, "GET", "https://gmail.googleapis.com/gmail/v1/users/me/messages", params=params)
            return {"messages": data.get("messages", []), "nextPageToken": data.get("nextPageToken")}
        if extension_id == "gmail" and action == "read":
            message_id = query.strip()
            if not message_id:
                raise RuntimeError("ต้องระบุ Gmail message id")
            data = self._request(extension_id, "GET", f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}", params={"format": "full"})
            return {"id": data.get("id"), "threadId": data.get("threadId"), "snippet": data.get("snippet"), "payload": data.get("payload", {})}
        if extension_id == "gmail" and action == "trash":
            message_id = query.strip()
            if not message_id: raise RuntimeError("ต้องระบุ Gmail message id")
            return self._request(extension_id, "POST", f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/trash", json={})
        if extension_id == "gmail" and action == "send":
            import base64, email.utils
            if "|" not in query:
                raise RuntimeError("รูปแบบส่งอีเมล: recipient | subject | body")
            recipient, subject, body = [part.strip() for part in query.split("|", 2)]
            raw = f"To: {recipient}\r\nSubject: {subject}\r\nDate: {email.utils.formatdate(localtime=True)}\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n{body}"
            encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode().rstrip("=")
            return self._request(extension_id, "POST", "https://gmail.googleapis.com/gmail/v1/users/me/messages/send", json={"raw": encoded})
        if extension_id == "gmail" and action == "news_report":
            import re as _re
            from app.search.public_web import search_web
            parts = [part.strip() for part in query.split("|", 2)]
            if len(parts) != 3 or not _re.fullmatch(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", parts[0]):
                raise RuntimeError("รูปแบบรายงานข่าว: recipient@example.com | หัวข้ออีเมล | คำค้นข่าว")
            recipient, subject, topic = parts
            results = search_web(topic)[:8]
            if not results: raise RuntimeError("ไม่พบแหล่งข่าวที่ใช้ทำรายงาน")
            lines = [f"รายงานข่าว: {topic}", "", "สรุปจากผลค้นหาสาธารณะ:"]
            for i, item in enumerate(results, 1):
                lines.append(f"{i}. {item.get('title') or item.get('snippet') or 'แหล่งข่าว'}\n{item.get('snippet','')}\n{item.get('url','')}")
            raw = f"To: {recipient}\r\nSubject: {subject}\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n" + "\n\n".join(lines)
            import base64
            encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode().rstrip("=")
            return self._request(extension_id, "POST", "https://gmail.googleapis.com/gmail/v1/users/me/messages/send", json={"raw": encoded})
        if extension_id == "drive" and action == "search":
            q = f"name contains '{query.replace(chr(39), chr(39)*2)}'" if query else "trashed = false"
            return self._request(extension_id, "GET", "https://www.googleapis.com/drive/v3/files", params={"q": q, "pageSize": 20, "fields": "files(id,name,mimeType,modifiedTime,webViewLink)"})
        if extension_id == "drive" and action == "read":
            file_id = query.strip()
            if not file_id: raise RuntimeError("ต้องระบุ Drive file id")
            meta = self._request(extension_id, "GET", f"https://www.googleapis.com/drive/v3/files/{file_id}", params={"fields": "id,name,mimeType,modifiedTime,webViewLink"})
            return meta
        if extension_id == "drive" and action == "create":
            if "|" not in query: raise RuntimeError("รูปแบบสร้างไฟล์: filename | content")
            name, content = [part.strip() for part in query.split("|", 1)]
            import json as _json, uuid as _uuid
            boundary = "jarvis_" + _uuid.uuid4().hex
            body = (
                f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
                + _json.dumps({"name": name, "mimeType": "text/plain"})
                + f"\r\n--{boundary}\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n"
                + content + f"\r\n--{boundary}--\r\n"
            ).encode("utf-8")
            token = self._access_token(extension_id)
            resp = requests.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,mimeType,modifiedTime,webViewLink",
                headers={"Authorization": f"Bearer {token}", "Content-Type": f"multipart/related; boundary={boundary}"},
                data=body, timeout=60,
            )
            resp.raise_for_status()
            return resp.json()
        if extension_id == "drive" and action == "delete":
            file_id = query.strip()
            if not file_id: raise RuntimeError("ต้องระบุ Drive file id")
            return self._request(extension_id, "DELETE", f"https://www.googleapis.com/drive/v3/files/{file_id}")
        if extension_id == "drive" and action == "update":
            if "|" not in query: raise RuntimeError("รูปแบบแก้ชื่อไฟล์ Drive: file_id | ชื่อใหม่")
            file_id, name = [part.strip() for part in query.split("|",1)]
            return self._request(extension_id, "PATCH", f"https://www.googleapis.com/drive/v3/files/{file_id}", json={"name":name})
        if extension_id == "calendar" and action == "upcoming":
            from datetime import datetime, timezone
            return self._request(extension_id, "GET", "https://www.googleapis.com/calendar/v3/calendars/primary/events", params={"singleEvents": "true", "orderBy": "startTime", "maxResults": 20, "timeMin": datetime.now(timezone.utc).isoformat()})
        if extension_id == "calendar" and action == "create":
            if "|" not in query: raise RuntimeError("รูปแบบสร้างปฏิทิน: title | start_iso | end_iso")
            title, start_iso, end_iso = [part.strip() for part in query.split("|", 2)]
            body={"summary":title,"start":{"dateTime":start_iso},"end":{"dateTime":end_iso}}
            return self._request(extension_id, "POST", "https://www.googleapis.com/calendar/v3/calendars/primary/events", json=body)
        if extension_id == "calendar" and action == "delete":
            event_id = query.strip()
            if not event_id: raise RuntimeError("ต้องระบุ Calendar event id")
            return self._request(extension_id, "DELETE", f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}")
        if extension_id == "calendar" and action == "update":
            if query.count("|") != 3: raise RuntimeError("รูปแบบแก้นัด: event_id | title | start_iso | end_iso")
            event_id, title, start_iso, end_iso = [part.strip() for part in query.split("|",3)]
            return self._request(extension_id, "PATCH", f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}", json={"summary":title,"start":{"dateTime":start_iso},"end":{"dateTime":end_iso}})
        if extension_id == "github" and action == "repos":
            return self._request(extension_id, "GET", "https://api.github.com/user/repos", params={"per_page": 30, "sort": "updated"})
        if extension_id == "github" and action == "read":
            if "/" not in query: raise RuntimeError("รูปแบบอ่านไฟล์ GitHub: owner/repo/path")
            owner, repo, path = query.split("/",2)
            return self._request(extension_id, "GET", f"https://api.github.com/repos/{owner}/{repo}/contents/{path}")
        if extension_id == "github" and action == "issue":
            if "|" not in query or "/" not in query: raise RuntimeError("รูปแบบ issue: owner/repo | title | body")
            repo_full, title, body = [part.strip() for part in query.split("|",2)]
            return self._request(extension_id, "POST", f"https://api.github.com/repos/{repo_full}/issues", json={"title":title,"body":body})
        if extension_id == "github" and action == "close_issue":
            if "|" not in query: raise RuntimeError("รูปแบบปิด issue: owner/repo | issue_number")
            repo_full, number = [part.strip() for part in query.split("|",1)]
            return self._request(extension_id, "PATCH", f"https://api.github.com/repos/{repo_full}/issues/{number}", json={"state":"closed"})
        if extension_id == "github" and action == "update_issue":
            if query.count("|") != 3: raise RuntimeError("รูปแบบแก้ issue: owner/repo | issue_number | title | body")
            repo_full, number, title, body = [part.strip() for part in query.split("|",3)]
            return self._request(extension_id, "PATCH", f"https://api.github.com/repos/{repo_full}/issues/{number}", json={"title":title,"body":body})
        if extension_id == "notion" and action == "search":
            body = {"page_size": 20}
            if query: body["query"] = query
            return self._request(extension_id, "POST", "https://api.notion.com/v1/search", json=body, headers={"Notion-Version": os.getenv("NOTION_VERSION", "2026-03-11"), "Content-Type": "application/json"})
        if extension_id == "notion" and action == "read":
            page_id = query.strip()
            if not page_id: raise RuntimeError("ต้องระบุ Notion page id")
            return self._request(extension_id, "GET", f"https://api.notion.com/v1/pages/{page_id}", headers={"Notion-Version": os.getenv("NOTION_VERSION", "2026-03-11")})
        if extension_id == "notion" and action == "update":
            if "|" not in query: raise RuntimeError("รูปแบบแก้ Notion: page_id | archived(true/false)")
            page_id, archived = [part.strip() for part in query.split("|",1)]
            return self._request(extension_id, "PATCH", f"https://api.notion.com/v1/pages/{page_id}", json={"archived": archived.lower()=="true"}, headers={"Notion-Version": os.getenv("NOTION_VERSION", "2026-03-11"), "Content-Type": "application/json"})
        raise RuntimeError(f"ไม่รองรับ action {action} สำหรับ {extension_id}")
