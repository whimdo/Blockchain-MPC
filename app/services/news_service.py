from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import requests
import yaml
from pymongo import DESCENDING

from app.clients.mongo_client import MongoDBClient
from app.models.news_models import NewsArticle, NewsLatestResponse, NewsSyncResponse
from app.utils.logging_config import get_logger
from configs.mongo_config import load_mongo_config


class NewsServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class NewsService:
    def __init__(self) -> None:
        self.logger = get_logger("app.services.news_service")
        self.mongo = MongoDBClient()
        self.mongo_cfg = load_mongo_config()
        self.config_path = Path(__file__).resolve().parents[2] / "configs" / "news_sources_config.yaml"

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _to_iso(value: str | None) -> str | None:
        if not value:
            return None
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except Exception:
            return value

    @staticmethod
    def _clean_html(value: str | None) -> str:
        text = re.sub(r"<[^>]+>", " ", value or "")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _article_id(url: str) -> str:
        return hashlib.sha1(url.strip().encode("utf-8")).hexdigest()

    def _collection(self):
        collection = self.mongo.collection(self.mongo_cfg.news_articles_collection)
        collection.create_index([("published_at", DESCENDING)])
        collection.create_index("category")
        collection.create_index("related_symbols")
        return collection

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise NewsServiceError(500, "NEWS_CONFIG_NOT_FOUND", "News config file not found.")
        with self.config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}

    def _category_rules(self, config: dict[str, Any]) -> dict[str, dict[str, Any]]:
        rules = config.get("category_rules") or {}
        return rules if isinstance(rules, dict) else {}

    def _tracked_symbols(self, config: dict[str, Any]) -> list[str]:
        symbols = config.get("tracked_symbols") or []
        return [str(item).upper() for item in symbols if str(item).strip()]

    def _detect_symbols(self, text: str, symbols: list[str]) -> list[str]:
        found: list[str] = []
        lower_text = text.lower()
        aliases = {"BTC": ["bitcoin", "btc"], "ETH": ["ethereum", "ether", "eth"]}
        for symbol in symbols:
            terms = aliases.get(symbol, [symbol.lower()])
            if any(re.search(rf"\b{re.escape(term.lower())}\b", lower_text) for term in terms):
                found.append(symbol)
        return found

    def _detect_category(self, text: str, default_category: str, rules: dict[str, dict[str, Any]]) -> tuple[str, str, list[str]]:
        lower_text = text.lower()
        best_category = default_category or "market"
        best_label = str(rules.get(best_category, {}).get("label") or best_category)
        matched_keywords: list[str] = []

        for category, rule in rules.items():
            keywords = [str(item).lower() for item in rule.get("keywords", []) if str(item).strip()]
            hits = [item for item in keywords if item in lower_text]
            if len(hits) > len(matched_keywords):
                best_category = str(category)
                best_label = str(rule.get("label") or category)
                matched_keywords = hits[:6]

        return best_category, best_label, matched_keywords

    def _parse_rss(self, source: dict[str, Any], config: dict[str, Any]) -> list[NewsArticle]:
        url = str(source.get("url", "")).strip()
        if not url:
            return []

        response = requests.get(url, timeout=20, headers={"User-Agent": "ChainPilot/0.1 RSS Reader"})
        response.raise_for_status()
        root = ET.fromstring(response.content)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []

        now = self._utc_now_iso()
        rules = self._category_rules(config)
        symbols = self._tracked_symbols(config)
        default_category = str(source.get("default_category") or "market")
        articles: list[NewsArticle] = []

        for item in items:
            title = self._clean_html(item.findtext("title"))
            link = (item.findtext("link") or "").strip()
            if not title or not link:
                continue
            summary = self._clean_html(item.findtext("description"))
            published_at = self._to_iso(item.findtext("pubDate"))
            text = f"{title} {summary}"
            category, label, keywords = self._detect_category(text, default_category, rules)
            articles.append(
                NewsArticle(
                    article_id=self._article_id(link),
                    title=title,
                    summary=summary[:420] if summary else None,
                    source=str(source.get("name") or "CoinDesk"),
                    url=link,
                    published_at=published_at,
                    category=category,
                    category_label=label,
                    related_symbols=self._detect_symbols(text, symbols),
                    related_keywords=keywords,
                    fetched_at=now,
                )
            )
        return articles

    def sync(self, limit: int = 30) -> NewsSyncResponse:
        config = self._load_config()
        sources = [
            item
            for item in config.get("news_sources", [])
            if isinstance(item, dict) and item.get("enabled", True) and item.get("type") == "rss"
        ]
        collection = self._collection()
        fetched: list[NewsArticle] = []
        upserted = 0

        for source in sources:
            try:
                fetched.extend(self._parse_rss(source, config))
            except Exception:
                self.logger.exception("Failed to sync news source=%s", source.get("name"))

        for article in fetched[: max(1, limit)]:
            payload = article.model_dump() if hasattr(article, "model_dump") else article.dict()
            result = collection.update_one(
                {"_id": article.article_id},
                {"$set": {**payload, "_id": article.article_id}},
                upsert=True,
            )
            if result.upserted_id is not None or result.modified_count:
                upserted += 1

        return NewsSyncResponse(
            source_count=len(sources),
            fetched_count=len(fetched),
            upserted_count=upserted,
            articles=fetched[:limit],
        )

    def latest(self, limit: int = 24, category: str | None = None, symbol: str | None = None) -> NewsLatestResponse:
        collection = self._collection()
        query: dict[str, Any] = {}
        if category and category != "all":
            query["category"] = category
        if symbol:
            query["related_symbols"] = symbol.upper()

        cursor = collection.find(query, sort=[("published_at", DESCENDING), ("fetched_at", DESCENDING)], limit=max(1, min(limit, 100)))
        articles: list[NewsArticle] = []
        for doc in cursor:
            doc.pop("_id", None)
            articles.append(NewsArticle(**doc))

        categories = sorted(collection.distinct("category"))
        return NewsLatestResponse(
            page_updated_at=self._utc_now_iso(),
            total=collection.count_documents(query),
            categories=categories,
            articles=articles,
        )
