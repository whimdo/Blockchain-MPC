from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


AIChatRole = Literal["user", "assistant", "system", "tool"]
AIChatMode = Literal["auto", "token", "dao", "proposal"]
AIToolStatus = Literal["success", "failed", "running", "skipped"]
AIPageStatus = Literal["idle", "loading", "tool_running", "success", "error"]
AIResultCardType = Literal["token", "dao", "proposal", "text"]
AIChatSessionStatus = Literal["active", "archived", "deleted"]


class ErrorResponse(BaseModel):
    code: str
    message: str


class AIChatMessage(BaseModel):
    message_id: str | None = None
    role: AIChatRole
    content: str
    created_at: datetime | None = None
    mode: AIChatMode | None = None
    tool_call_ids: list[str] = Field(default_factory=list)


class AIChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(..., min_length=1, max_length=500)
    mode: AIChatMode = "auto"
    history: list[AIChatMessage] = Field(default_factory=list)
    user_id: str | None = None
    client: str | None = "web"


class AIToolCallRecord(BaseModel):
    tool_call_id: str | None = None
    tool_name: str
    status: AIToolStatus = "success"
    created_at: datetime | None = None


class AIResultCard(BaseModel):
    card_type: AIResultCardType
    title: str
    subtitle: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    action_label: str | None = None
    action_value: str | None = None


class AIIntentResult(BaseModel):
    mode: AIChatMode
    confidence: float | None = Field(default=None, ge=0, le=1)
    entities: dict[str, Any] = Field(default_factory=dict)
    required_tools: list[str] = Field(default_factory=list)


class AIChatResponse(BaseModel):
    session_id: str
    answer: str
    mode: AIChatMode = "auto"
    status: AIPageStatus = "success"
    used_tools: list[AIToolCallRecord] = Field(default_factory=list)
    result_cards: list[AIResultCard] = Field(default_factory=list)
    error_message: str | None = None


class AIChatSessionMetadata(BaseModel):
    user_id: str | None = None
    client: str | None = "web"
    message_count: int = 0
    tool_call_count: int = 0


class AIChatSessionDocument(BaseModel):
    """MongoDB document stored in ai_chat_sessions, using session_id as _id."""

    session_id: str
    title: str | None = None
    mode: AIChatMode = "auto"
    status: AIChatSessionStatus = "active"
    created_at: datetime
    updated_at: datetime
    messages: list[AIChatMessage] = Field(default_factory=list)
    tool_calls: list[AIToolCallRecord] = Field(default_factory=list)
    metadata: AIChatSessionMetadata = Field(default_factory=AIChatSessionMetadata)


class AIChatSessionSummary(BaseModel):
    session_id: str
    title: str | None = None
    mode: AIChatMode = "auto"
    status: AIChatSessionStatus = "active"
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: str | None = None


class AIChatSessionListResponse(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0
    sessions: list[AIChatSessionSummary] = Field(default_factory=list)


class AIChatSessionCreateRequest(BaseModel):
    title: str | None = None
    mode: AIChatMode = "auto"
    user_id: str | None = None
    client: str | None = "web"


class AIChatSessionUpdateRequest(BaseModel):
    title: str | None = None
    status: AIChatSessionStatus | None = None


class AISessionState(BaseModel):
    session_id: str
    status: AIPageStatus = "idle"
    mode: AIChatMode = "auto"
    messages: list[AIChatMessage] = Field(default_factory=list)
    used_tools: list[AIToolCallRecord] = Field(default_factory=list)
