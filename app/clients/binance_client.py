from __future__ import annotations

from typing import Any
import json

import requests

from app.utils.logging_config import get_logger
from configs.provider_config import load_provider_config


class BinanceClient:
    """Client for Binance spot market API."""

    def __init__(self) -> None:
        """Initialize Binance client and load API base URL."""
        self.logger = get_logger("app.clients.binance_client")
        config = load_provider_config()
        self.base_url = config.binance_api_url

    def get_symbol_price(self, symbol: str) -> dict[str, Any]:
        """Fetch latest price for one trading pair."""
        url = f"{self.base_url}/api/v3/ticker/price"
        try:
            self.logger.info("Fetching single symbol price symbol=%s", symbol)
            response = requests.get(url, params={"symbol": symbol.upper()}, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception:
            self.logger.exception("Failed to fetch single symbol price symbol=%s", symbol)
            raise

    def get_multi_symbol_price(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Fetch latest prices for multiple trading pairs."""
        url = f"{self.base_url}/api/v3/ticker/price"
        try:
            self.logger.info("Fetching multiple symbol prices symbols=%s", symbols)
            response = requests.get(
                url,
                params={
                    "symbols": json.dumps([s.upper() for s in symbols], separators=(",", ":"))
                },
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else [data]
        except Exception:
            self.logger.exception("Failed to fetch multiple symbol prices symbols=%s", symbols)
            raise
