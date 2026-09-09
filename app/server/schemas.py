from pydantic import BaseModel, Field
from typing import Any, Optional


class SessionCreate(BaseModel):
    title: Optional[str] = None


class ChatRequest(BaseModel):
    text: str = Field(min_length=1)
    session_id: Optional[str] = None
    mode: str = Field(default="general")


class ConfirmationRequest(BaseModel):
    confirmed: bool


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: str
    source: str = "general"
    route: str = "memory_llm"
    requires_confirmation: bool = False
    metadata: dict[str, Any] = {}


class ExtensionActionRequest(BaseModel):
    action: str
    query: str | None = None


class ModelSelectRequest(BaseModel):
    model: str = Field(min_length=1, max_length=500)
    backend: str | None = None

class ConfirmationMessage(BaseModel):
    session_id: str
    approved: bool
