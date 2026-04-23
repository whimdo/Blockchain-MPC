from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
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

    def save_token_current_price(
        self,
        symbol: str,
        binance_price: float | Decimal | str,
        ankr_price: float | Decimal | str,
    ) -> dict[str, Any]:
        """
        Save current token price and keep latest 50 history records.

        MongoDB document structure example:
        {
            "symbol": "ETH",
            "source": "token_price",
            "current_price": {
                "binance_price": 1800.12,
                "ankr_price": 1799.98,
                "timestamp": datetime(...)
            },
            "price_history": [
                {
                    "binance_price": 1800.12,
                    "ankr_price": 1799.98,
                    "timestamp": datetime(...)
                }
            ],
            "created_at": datetime(...),
            "updated_at": datetime(...)
        }
        """
        now = self._now_utc()

        price_record = {
            "binance_price": float(binance_price),
            "ankr_price": float(ankr_price),
            "timestamp": now,
        }

        result = self.mongo_client.collection(
            self.config.token_prices_collection
        ).find_one_and_update(
            {"symbol": symbol},
            {
                "$set": {
                    "symbol": symbol,
                    "current_price": price_record,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
                "$push": {
                    "price_history": {
                        "$each": [price_record],
                        "$position": 0,
                        "$slice": 50,
                    }
                },
            },
            upsert=True,
            return_document=True,
        )

        return str(result["_id"])


    def save_ankr_token_price(
            self,
            symbol: str,
            price: float | Decimal | str,
            price_time: datetime | None = None,
        ) -> str:
            """
            Save latest Ankr token price and keep latest 50 Ankr history records.
            """
            now = self._now_utc()
            record_time = price_time or now

            ankr_record = {
                "price": float(price),
                "updated_at": record_time,
            }

            doc = self.mongo_client.collection(
                self.config.token_prices_collection
            ).find_one_and_update(
                {
                    "symbol": symbol,
                },
                {
                    "$set": {
                        "source": "token_price",
                        "symbol": symbol,
                        "ankr_current": ankr_record,
                        "updated_at": now,
                    },
                    "$setOnInsert": {
                        "created_at": now,
                    },
                    "$push": {
                        "ankr_history": {
                            "$each": [ankr_record],
                            "$position": 0,
                            "$slice": 50,
                        }
                    },
                },
                upsert=True,
                return_document=True,
            )

            return str(doc["_id"])

    def save_binance_token_price(
        self,
        symbol: str,
        price: float | Decimal | str,
        price_time: datetime | None = None,
    ) -> str:
        """
        Save latest Binance token price and keep latest 50 Binance history records.
        """
        now = self._now_utc()
        record_time = price_time or now

        binance_record = {
            "price": float(price),
            "updated_at": record_time,
        }

        doc = self.mongo_client.collection(
            self.config.token_prices_collection
        ).find_one_and_update(
            {
                "symbol": symbol,
            },
            {
                "$set": {
                    "source": "token_price",
                    "symbol": symbol,
                    "binance_current": binance_record,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
                "$push": {
                    "binance_history": {
                        "$each": [binance_record],
                        "$position": 0,
                        "$slice": 50,
                    }
                },
            },
            upsert=True,
            return_document=True,
        )

        return str(doc["_id"])
    
    def save_token_current_price_new(
        self,
        symbol: str,
        binance_price: float | Decimal | str,
        ankr_price: float | Decimal | str,
    )->list[str]:
            try:
                binanc_result = self.save_binance_token_price(symbol, binance_price)
                ankr_result = self.save_ankr_token_price(symbol, ankr_price)
                return [binanc_result, ankr_result]
            except Exception:
                self.logger.exception("Failed to save token price symbol=%s", symbol)
                raise
    
    def find_token_price(self, symbol: str) -> float:
        """Find token price by symbol."""
        doc = self.mongo_client.collection(self.config.token_prices_collection).find_one({"symbol": symbol})
        if not doc:
            raise ValueError(f"No price record found for symbol: {symbol}")
        binance_price = doc.get("binance_current", {}).get("price")
        ankr_price = doc.get("ankr_current", {}).get("price")
        if binance_price is not None:
            return binance_price
        elif ankr_price is not None:
            return ankr_price
        else:
            raise ValueError(f"No valid price found for symbol: {symbol}")
        
    def find_token_price_and_updated_at(self, symbol: str) -> dict[str, Any]:
        """Find token price and updated_at by symbol."""
        doc = self.mongo_client.collection(self.config.token_prices_collection).find_one({"symbol": symbol})
        if not doc:
            raise ValueError(f"No price record found for symbol: {symbol}")
        binance_price = doc.get("binance_current", {}).get("price")
        ankr_price = doc.get("ankr_current", {}).get("price")
        updated_at = doc.get("updated_at")
        if binance_price is not None:
            return {"price": binance_price, "updated_at": updated_at}
        elif ankr_price is not None:
            return {"price": ankr_price, "updated_at": updated_at}
        else:
            raise ValueError(f"No valid price found for symbol: {symbol}")