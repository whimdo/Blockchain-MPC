from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.clients.mongo_client import MongoDBClient
from app.utils.logging_config import get_logger
from configs.mongo_config import load_mongo_config


class MarketStorage:
    """MongoDB storage for market query results."""

    def __init__(self) -> None:
        self.logger = get_logger("app.storage.market_storage")
        self.config = load_mongo_config()
        self.mongo_client = MongoDBClient()

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    def save_ankr_raw_assets(
        self,
        address: str,
        chains: list[str],
        ankr_result: dict[str, Any],
    ) -> str:
        """Store raw response returned by Ankr."""
        doc = {
            "source": "ankr",
            "address": address,
            "chains": chains,
            "created_at": self._now_utc(),
            "payload": ankr_result,
        }
        result = self.mongo_client.collection(self.config.ankr_raw_collection).insert_one(doc)
        return str(result.inserted_id)

    def save_binance_prices(
        self,
        symbols: list[str],
        prices_result: Any,
    ) -> str:
        """Store response returned by Binance."""
        doc = {
            "source": "binance",
            "symbols": symbols,
            "created_at": self._now_utc(),
            "payload": prices_result,
        }
        result = self.mongo_client.collection(self.config.binance_prices_collection).insert_one(doc)
        return str(result.inserted_id)

    def save_asset_overview(
        self,
        address: str,
        chains: list[str],
        overview_result: dict[str, Any],
    ) -> str:
        """Store aggregated wallet overview result."""
        doc = {
            "source": "market_overview",
            "address": address,
            "chains": chains,
            "created_at": self._now_utc(),
            "payload": overview_result,
        }
        result = self.mongo_client.collection(self.config.asset_overviews_collection).insert_one(doc)
        return str(result.inserted_id)
