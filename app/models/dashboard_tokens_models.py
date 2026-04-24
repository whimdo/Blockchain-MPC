from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str


class TokenCard(BaseModel):
    symbol: str
    name: str
    display_name: str
    primary_chain: str
    category: str
    logo: str
    price: float | None
    price_display: str
    updated_at: str | None
    status: str
    tags: list[str] = Field(default_factory=list)


class TokenGroup(BaseModel):
    group_name: str
    group_key: str
    cards: list[TokenCard] = Field(default_factory=list)


class TokenOverviewResponse(BaseModel):
    page_updated_at: str
    total_tokens: int
    group_count: int
    groups: list[TokenGroup] = Field(default_factory=list)


class TokenRefreshRequest(BaseModel):
    symbol: str = Field(..., description="Token symbol to refresh, e.g. ETH")


class TokenRefreshGroup(BaseModel):
    group_name: str
    group_key: str
    cards: list[TokenCard] = Field(default_factory=list)


class TokenRefreshAllResponse(BaseModel):
    page_updated_at: str
    total_tokens: int
    group_count: int
    groups: list[TokenRefreshGroup] = Field(default_factory=list)

