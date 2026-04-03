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

        # 缓存 Binance 支持的交易对
        self._supported_symbols: set[str] | None = None

    def get_symbol_price(self, symbol: str) -> dict[str, Any]:
        """Fetch latest price for one trading pair."""
        url = f"{self.base_url}/api/v3/ticker/price"
        try:
            symbol = symbol.upper()
            self.logger.info("Fetching single symbol price symbol=%s", symbol)
            response = requests.get(url, params={"symbol": symbol}, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception:
            self.logger.exception("Failed to fetch single symbol price symbol=%s", symbol)
            raise

    def get_multi_symbol_price(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Fetch latest prices for multiple trading pairs."""
        url = f"{self.base_url}/api/v3/ticker/price"
        try:
            symbols = [s.upper() for s in symbols]
            self.logger.info("Fetching multiple symbol prices count=%s", len(symbols))

            response = requests.get(
                url,
                params={
                    "symbols": json.dumps(symbols, separators=(",", ":"))
                },
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else [data]
        except Exception:
            self.logger.exception("Failed to fetch multiple symbol prices symbols=%s", symbols)
            raise

    def get_exchange_symbols(self, force_refresh: bool = False) -> set[str]:
        """
        获取 Binance 当前支持的全部交易对，并缓存到内存。
        """
        if self._supported_symbols is not None and not force_refresh:
            return self._supported_symbols

        url = f"{self.base_url}/api/v3/exchangeInfo"
        try:
            self.logger.info("Fetching Binance exchange symbols")
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()

            symbols = {
                item["symbol"].upper()
                for item in data.get("symbols", [])
                if isinstance(item, dict) and "symbol" in item
            }

            self._supported_symbols = symbols
            self.logger.info("Loaded Binance exchange symbols count=%s", len(symbols))
            return symbols
        except Exception:
            self.logger.exception("Failed to fetch Binance exchange symbols")
            raise

    def filter_supported_symbols(self, symbols: list[str]) -> list[str]:
        """
        过滤掉 Binance 不支持的 symbol。
        """
        supported = self.get_exchange_symbols()
        input_symbols = [s.upper() for s in symbols]

        valid_symbols = [s for s in input_symbols if s in supported]
        invalid_symbols = [s for s in input_symbols if s not in supported]

        self.logger.info(
            "Filter symbols total=%s valid=%s invalid=%s",
            len(input_symbols),
            len(valid_symbols),
            len(invalid_symbols),
        )

        if invalid_symbols:
            self.logger.warning("Unsupported Binance symbols: %s", invalid_symbols)

        return valid_symbols

    def get_multi_symbol_price_safe(
        self,
        symbols: list[str],
        batch_size: int = 20,
    ) -> list[dict[str, Any]]:
        """
        安全批量查询：
        1. 先过滤 Binance 不支持的交易对
        2. 再按 batch_size 分批查询
        """
        valid_symbols = self.filter_supported_symbols(symbols)
        if not valid_symbols:
            self.logger.warning("No valid Binance symbols to query")
            return []
        all_results: list[dict[str, Any]] = []

        for i in range(0, len(valid_symbols), batch_size):
            batch = valid_symbols[i:i + batch_size]
            try:
                self.logger.info(
                    "Fetching Binance symbol batch index=%s size=%s",
                    i // batch_size,
                    len(batch),
                )
                results = self.get_multi_symbol_price(batch)
                all_results.extend(results)
            except Exception:
                self.logger.exception("Failed Binance batch query batch=%s", batch)

        self.logger.info("Fetched Binance prices total=%s", len(all_results))
        return all_results
