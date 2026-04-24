from __future__ import annotations

from typing import Any

import requests

from app.utils.logging_config import get_logger
from configs.provider_config import load_provider_config


class TokenDetailMarketClient:
    """Market data client for token detail page demo."""

    def __init__(self) -> None:
        self.logger = get_logger("app.clients.token_detail_market_client")
        config = load_provider_config()
        self.base_url = config.binance_api_url

    def get_24hr_ticker(self, symbol: str) -> dict[str, Any]:
        """Fetch 24h ticker stats for a Binance symbol."""
        url = f"{self.base_url}/api/v3/ticker/24hr"
        symbol = (symbol or "").upper()
        self.logger.info("Fetching 24hr ticker symbol=%s", symbol)
        response = requests.get(url, params={"symbol": symbol}, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {}

    def get_klines(self, symbol: str, interval: str, limit: int) -> list[list[Any]]:
        """Fetch kline points for chart rendering."""
        url = f"{self.base_url}/api/v3/klines"
        symbol = (symbol or "").upper()
        self.logger.info("Fetching klines symbol=%s interval=%s limit=%s", symbol, interval, limit)
        response = requests.get(
            url,
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []
