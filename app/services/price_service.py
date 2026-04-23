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

    @staticmethod
    def _prepare_symbol_for_binance(symbol: str) -> tuple[str, str]:
        """Return (base_symbol, binance_pair_symbol)."""
        base_symbol = SymbolConvertService.map_to_binance_base_symbol(symbol)
        binance_symbol = SymbolConvertService.to_binance_symbol(base_symbol)
        return base_symbol, binance_symbol

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
            base_symbol, binance_symbol = self._prepare_symbol_for_binance(symbol)
            if price is None:
                price_record = self.client.get_symbol_price(binance_symbol)
                self.logger.info("Fetched token price from Binance symbol=%s price=%s", binance_symbol, price_record.get("price"))
                price = price_record.get("price")
            else:
                price = str(price)
                self.logger.info("Using provided token price symbol=%s price=%s", base_symbol, price)
            try:
                result = self.storage.save_binance_token_price(base_symbol, price)
                self.logger.info("Updated token current price id=%s symbol=%s", result, base_symbol)
                return result
            except Exception:
                self.logger.exception("Failed to update token current price symbol=%s", base_symbol)
                raise
        except Exception:
            self.logger.exception("Failed to fetch token price from Binance symbol=%s", symbol)
            raise
    
    def update_get_binance_token_price_tuple(self, symbol: str, price: float = None) -> tuple[str, dict[str, Any]]:
        """Update Binance current price for a token.

        Returns:
            tuple(
                result_from_storage,
                compact_binance_price={"symbol": "...", "price": "..."}
            )
        """
        try:
            base_symbol, binance_symbol = self._prepare_symbol_for_binance(symbol)
            if price is None:
                price_record = self.client.get_symbol_price(binance_symbol)
                self.logger.info("Fetched token price from Binance symbol=%s price=%s", binance_symbol, price_record.get("price"))
                price = price_record.get("price")
            else:
                price = str(price)
                self.logger.info("Using provided token price symbol=%s price=%s", base_symbol, price)
            try:
                result = self.storage.save_binance_token_price(base_symbol, price)
                self.logger.info("Updated token current price id=%s symbol=%s", result, base_symbol)
                compact_price_record = {
                    "symbol": binance_symbol,
                    "price": price,
                }
                return result, compact_price_record
            except Exception:
                self.logger.exception("Failed to update token current price symbol=%s", base_symbol)
                raise
        except Exception:
            self.logger.exception("Failed to fetch token price from Binance symbol=%s", symbol)
            raise

    def update_get_binance_tokens_price(self, symbols: list[str], prices: list[float] = None) -> list[dict[str, Any]]:
        """Update Binance current prices for multiple tokens."""
        try:
            if prices is None:
                binance_symbols = SymbolConvertService.to_binance_symbols(symbols)
                price_records = self.client.get_multi_symbol_price_safe(binance_symbols)
                self.logger.info("Fetched token prices from Binance symbols=%s", symbols)
                prices = [record.get("price") for record in price_records]
            else:
                prices = [str(price) for price in prices]
                self.logger.info("Using provided token prices symbols=%s", symbols)

            try:
                result = self.storage.save_binance_tokens_price(symbols, prices)
                self.logger.info("Updated token current prices inserted_id=%s symbols=%s", result, symbols)
                return result
            except Exception:
                self.logger.exception("Failed to update token current prices symbols=%s", symbols)
                raise
        except Exception:
            self.logger.exception("Failed to fetch token prices from Binance symbols=%s", symbols)
            raise

    def update_get_binance_tokens_price_tuple(
        self,
        symbols: list[str],
        prices: list[float] = None,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Update Binance current prices for multiple tokens.

        Returns:
            tuple(
                result_from_storage,
                compact_binance_prices=[{"symbol": "...", "price": "..."}]
            )
        """
        try:
            if prices is None:
                binance_symbols = SymbolConvertService.to_binance_symbols(symbols)
                price_records = self.client.get_multi_symbol_price_safe(binance_symbols)
                compact_price_records = [
                    {
                        "symbol": record.get("symbol"),
                        "price": record.get("price"),
                    }
                    for record in price_records
                    if isinstance(record, dict)
                ]
                self.logger.info("Fetched token prices from Binance symbols=%s", symbols)
                prices = [record.get("price") for record in price_records]
            else:
                compact_price_records = [
                    {
                        "symbol": symbol,
                        "price": str(price),
                    }
                    for symbol, price in zip(symbols, prices)
                ]
                prices = [str(price) for price in prices]
                self.logger.info("Using provided token prices symbols=%s", symbols)

            try:
                result = self.storage.save_binance_tokens_price(symbols, prices)
                self.logger.info("Updated token current prices inserted_id=%s symbols=%s", result, symbols)
                return result, compact_price_records
            except Exception:
                self.logger.exception("Failed to update token current prices symbols=%s", symbols)
                raise
        except Exception:
            self.logger.exception("Failed to fetch token prices from Binance symbols=%s", symbols)
            raise
    


    def update_get_ankr_token_price(self, symbol: str, price: float = None) -> dict[str, Any]:
        """Update ankr current price for a token.if price is NULL fetch from Binance."""
        try:
            base_symbol, binance_symbol = self._prepare_symbol_for_binance(symbol)
            if price is None:
                price_record = self.client.get_symbol_price(binance_symbol)
                self.logger.info("Fetched token price from Binance symbol=%s price=%s", binance_symbol, price_record.get("price"))
                price = price_record.get("price")
            else:
                price = str(price)
                self.logger.info("Using provided token price symbol=%s price=%s", base_symbol, price)

            try:
                result = self.storage.save_ankr_token_price(base_symbol, price)
                self.logger.info("Updated Ankr token current price id=%s symbol=%s", result, base_symbol)
                return result
            except Exception:
                self.logger.exception("Failed to update Ankr token current price symbol=%s", base_symbol)
                raise
        except Exception:
            self.logger.exception("Failed to fetch token price from Binance symbol=%s", symbol)
            raise
    
    def update_get_ankr_token_price_tuple(self, symbol: str, price: float = None) -> tuple[str, dict[str, Any]]:
        """Update Ankr current price for one token and return compact tuple payload."""
        try:
            base_symbol, binance_symbol = self._prepare_symbol_for_binance(symbol)
            if price is None:
                price_record = self.client.get_symbol_price(binance_symbol)
                self.logger.info("Fetched token price from Binance symbol=%s price=%s", binance_symbol, price_record.get("price"))
                price = price_record.get("price")
            else:
                price = str(price)
                self.logger.info("Using provided token price symbol=%s price=%s", base_symbol, price)

            try:
                result = self.storage.save_ankr_token_price(base_symbol, price)
                self.logger.info("Updated Ankr token current price id=%s symbol=%s", result, base_symbol)
                compact_price_record = {
                    "symbol": binance_symbol,
                    "price": price,
                }
                return result, compact_price_record
            except Exception:
                self.logger.exception("Failed to update Ankr token current price symbol=%s", base_symbol)
                raise
        except Exception:
            self.logger.exception("Failed to fetch token price from Binance symbol=%s", symbol)
            raise
    
    def update_get_token_price(self,symbol:str,ankr_price:float = None,binance_price:float = None) -> dict[str, Any]:
        """Update token price for a token.if price is NULL fetch from Binance."""
        try:
            symbol, binance_symbol = self._prepare_symbol_for_binance(symbol)
            if binance_price is None:
                binance_price = self.client.get_symbol_price(binance_symbol).get("price")
                self.logger.info("Using provided Binance token price symbol=%s price=%s", binance_symbol, binance_price)

            if ankr_price is None:
                ankr_price = binance_price
                self.logger.info("Using Binance token price symbol=%s price=%s to alternative Ankr", symbol, binance_price)

            try:
                result = self.storage.save_token_current_price_new(symbol, binance_price, ankr_price)
                self.logger.info("Updated token current price id=%s symbol=%s", result, symbol)
                return result
            except Exception:
                self.logger.exception("Failed to update token current price symbol=%s", symbol)
                raise
        except Exception:
            self.logger.exception("Failed to fetch token price from Binance symbol=%s", symbol)
            raise
    
    def update_get_token_price_tuple(
        self,
        symbol: str,
        ankr_price: float = None,
        binance_price: float = None,
    ) -> tuple[list[str], dict[str, Any]]:
        """Update combined token prices and return compact tuple payload."""
        try:
            symbol, binance_symbol = self._prepare_symbol_for_binance(symbol)
            if binance_price is None:
                binance_price = self.client.get_symbol_price(binance_symbol).get("price")
                self.logger.info("Using provided Binance token price symbol=%s price=%s", binance_symbol, binance_price)

            if ankr_price is None:
                ankr_price = binance_price
                self.logger.info("Using Binance token price symbol=%s price=%s to alternative Ankr", symbol, binance_price)

            try:
                result = self.storage.save_token_current_price_new(symbol, binance_price, ankr_price)
                self.logger.info("Updated token current price id=%s symbol=%s", result, symbol)
                compact_price_record = {
                    "symbol": symbol,
                    "binance_price": str(binance_price),
                    "ankr_price": str(ankr_price),
                }
                return result, compact_price_record
            except Exception:
                self.logger.exception("Failed to update token current price symbol=%s", symbol)
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
