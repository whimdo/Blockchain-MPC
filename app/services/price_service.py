from typing import Any

from app.clients.binance_client import BinanceClient
from app.storage.market_storage import MarketStorage
from app.utils.logging_config import get_logger
from app.services.symbol_mapper_service import SymbolConvertService


class PriceService:
    """Service for market price queries."""

    def __init__(self) -> None:
        """Initialize price service."""
        self.logger = get_logger("app.services.price_service")
        self.client = BinanceClient()
        self.storage = MarketStorage()

    def get_symbol_price(self, symbol: str) -> dict:
        """Get price for one trading pair."""
        try:
            result = self.client.get_symbol_price(symbol)
            try:
                inserted_id = self.storage.save_binance_prices([symbol], result)
                self.logger.info("Stored Binance single price inserted_id=%s symbol=%s", inserted_id, symbol)
                # id = self.storage.save_token_current_price(symbol, result.get("price"))
                # self.logger.info("Stored token current price id=%s symbol=%s", id, symbol)
            except Exception:
                self.logger.exception("Failed to store Binance single price symbol=%s", symbol)
            self.logger.info("Single symbol price fetched symbol=%s", symbol)
            return result
        except Exception:
            self.logger.exception("Single symbol price fetch failed symbol=%s", symbol)
            raise

    def get_symbols_price(self, symbols: list[str]) -> list[dict]:
        """Get prices for multiple trading pairs."""
        try:
            result = self.client.get_multi_symbol_price_safe(symbols)
            try:
                inserted_id = self.storage.save_binance_prices(symbols, result)
                self.logger.info(
                    "Stored Binance multi prices inserted_id=%s requested_count=%s",
                    inserted_id,
                    len(symbols),
                )
            except Exception:
                self.logger.exception("Failed to store Binance multi prices symbols=%s", symbols)
            self.logger.info("Multiple symbol prices fetched count=%s", len(symbols))
            return result
        except Exception:
            self.logger.exception("Multiple symbol prices fetch failed symbols=%s", symbols)
            raise

    def update_get_binance_token_price(self, symbol: str, price: float = None) -> dict[str, Any]:
        """Update binance current price for a token."""
        try:
            if price is None:
                price_record = self.client.get_symbol_price(symbol)
                self.logger.info("Fetched token price from Binance symbol=%s price=%s", symbol, price_record.get("price"))
                price = price_record.get("price")
            else:
                price = str(price)
                self.logger.info("Using provided token price symbol=%s price=%s", symbol, price)
            try:
                result = self.storage.save_binance_token_price(symbol, price)
                self.logger.info("Updated token current price id=%s symbol=%s", result, symbol)
                return result
            except Exception:
                self.logger.exception("Failed to update token current price symbol=%s", symbol)
                raise
        except Exception:
            self.logger.exception("Failed to fetch token price from Binance symbol=%s", symbol)
            raise

    def update_get_ankr_token_price(self, symbol: str, price: float = None) -> dict[str, Any]:
        """Update ankr current price for a token."""
        try:
            symbol = SymbolConvertService.map_to_binance_base_symbol(symbol)
            if price is None:
                price_record = self.client.get_symbol_price(symbol)
                self.logger.info("Fetched token price from Binance symbol=%s price=%s", symbol, price_record.get("price"))
                price = price_record.get("price")
            else:
                price = str(price)
                self.logger.info("Using provided token price symbol=%s price=%s", symbol, price)
            try:
                result = self.storage.save_ankr_token_price(symbol, price)
                self.logger.info("Updated Ankr token current price id=%s symbol=%s", result, symbol)
                return result
            except Exception:
                self.logger.exception("Failed to update Ankr token current price symbol=%s", symbol)
                raise
        except Exception:
            self.logger.exception("Failed to fetch token price from Binance symbol=%s", symbol)
            raise

    def find_token_price(self, symbol: str) -> dict[str, Any]:
        """Find token price by symbol."""
        try:
            result = self.storage.find_token_price_and_updated_at(symbol)
            self.logger.info("Token price found for symbol=%s", symbol)
            return result
        except Exception:
            self.logger.exception("Failed to find token price for symbol=%s", symbol)
            raise