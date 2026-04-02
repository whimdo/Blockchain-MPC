from __future__ import annotations

from typing import Any
import json
import requests
from configs.provider_config import load_provider_config


class BinanceClient:
    """
    Binance Spot API ¿Í»§¶Ë
    """

    def __init__(self) -> None:
        config = load_provider_config()
        self.base_url = config.binance_api_url

    def get_symbol_price(self, symbol: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/v3/ticker/price"
        response = requests.get(url, params={"symbol": symbol.upper()}, timeout=15)
        response.raise_for_status()
        return response.json()

    def get_multi_symbol_price(self, symbols: list[str]) -> list[dict[str, Any]]:
        url = f"{self.base_url}/api/v3/ticker/price"
        response = requests.get(
            url,
            params={"symbols": json.dumps([s.upper() for s in symbols])},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else [data]