from app.clients.binance_client import BinanceClient
from app.storage.market_storage import MarketStorage
from app.utils.logging_config import get_logger


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
