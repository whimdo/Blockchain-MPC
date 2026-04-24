from __future__ import annotations

from typing import Any

from app.clients.binance_client import BinanceClient


class TokenDetailMarketClient:
    """Compatibility wrapper for token detail market APIs.

    Note:
    Direct Binance HTTP calls are centralized in BinanceClient.
    """

    def __init__(self) -> None:
        self.client = BinanceClient()

    def get_24hr_ticker(self, symbol: str) -> dict[str, Any]:
        return self.client.get_24hr_ticker(symbol)

    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> list[list[Any]]:
        return self.client.get_klines(symbol, interval, limit)
