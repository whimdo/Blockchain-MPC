from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str


class NewsArticle(BaseModel):
    article_id: str
    title: str
    summary: str | None = None
    source: str
    url: str
    published_at: str | None = None
    category: str = "market"
    category_label: str = "市场行情"
    related_symbols: list[str] = Field(default_factory=list)
    related_keywords: list[str] = Field(default_factory=list)
    fetched_at: str


class NewsLatestResponse(BaseModel):
    page_updated_at: str
    total: int = 0
    categories: list[str] = Field(default_factory=list)
    articles: list[NewsArticle] = Field(default_factory=list)


class NewsSyncResponse(BaseModel):
    source_count: int
    fetched_count: int
    upserted_count: int
    articles: list[NewsArticle] = Field(default_factory=list)
