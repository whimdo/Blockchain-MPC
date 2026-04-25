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
    tool_name: str | None = None
    tool_call_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


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
    description: str | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    status: AIToolStatus = "success"
    duration_ms: int | None = Field(default=None, ge=0)
    data_source: list[str] = Field(default_factory=list)
    error_message: str | None = None
    result_summary: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIContextToken(BaseModel):
    symbol: str
    name: str | None = None
    price_display: str | None = None
    change_percent: float | None = None
    chart_range: str | None = None
    source: list[str] = Field(default_factory=list)


class AIContextDao(BaseModel):
    space_id: str
    name: str | None = None
    proposal_count: int | None = None
    last_synced_at: datetime | None = None
    source: list[str] = Field(default_factory=list)


class AIContextProposal(BaseModel):
    proposal_id: str
    title: str | None = None
    space_id: str | None = None
    state: str | None = None
    author: str | None = None
    keywords: list[str] = Field(default_factory=list)
    similarity_score: float | None = None
    is_vectorized: bool | None = None
    source: list[str] = Field(default_factory=list)


class AIChatContext(BaseModel):
    tokens: list[AIContextToken] = Field(default_factory=list)
    daos: list[AIContextDao] = Field(default_factory=list)
    proposals: list[AIContextProposal] = Field(default_factory=list)


class AISuggestedQuestion(BaseModel):
    text: str
    mode: AIChatMode = "auto"
    category: str | None = None


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
    context: AIChatContext | None = None
    result_cards: list[AIResultCard] = Field(default_factory=list)
    suggested_questions: list[AISuggestedQuestion] = Field(default_factory=list)
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
    context: AIChatContext = Field(default_factory=AIChatContext)
    suggested_questions: list[AISuggestedQuestion] = Field(default_factory=list)
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
    context: AIChatContext = Field(default_factory=AIChatContext)
