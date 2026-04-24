from __future__ import annotations

from app.models.symbol_mapper import COMMON_TOKEN_TO_BINANCE_BASE


class SymbolConvertService:
    """Service for converting raw token symbols to Binance trading symbols."""

    @staticmethod
    def normalize_token_symbol(symbol: str) -> str:
        """
        Normalize raw token symbol.

        Rules:
        1. strip whitespace
        2. uppercase
        3. remove common suffix variants such as .E / -E / _E
        """
        if not symbol or not symbol.strip():
            raise ValueError("symbol cannot be empty")

        normalized = symbol.strip().upper()

        suffixes = [".E", "-E", "_E"]
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
                break

        return normalized

    @staticmethod
    def map_to_binance_base_symbol(symbol: str) -> str:
        """
        Convert normalized token symbol to Binance base asset symbol.

        Example:
            WETH -> ETH
            WBTC -> BTC
            ETH -> ETH
        """
        normalized = SymbolConvertService.normalize_token_symbol(symbol)
        return COMMON_TOKEN_TO_BINANCE_BASE.get(normalized, normalized)

    @staticmethod
    def to_binance_symbol(symbol: str, quote_asset: str = "USDT") -> str:
        """
        Convert token symbol to Binance trading pair symbol.

        Example:
            ETH -> ETHUSDT
            WETH -> ETHUSDT
            WBTC -> BTCUSDT
        """
        if not quote_asset or not quote_asset.strip():
            raise ValueError("quote_asset cannot be empty")

        base_symbol = SymbolConvertService.map_to_binance_base_symbol(symbol)
        quote_symbol = quote_asset.strip().upper()

        return f"{base_symbol}{quote_symbol}"
    
    @staticmethod
    def to_binance_symbols(symbols: list[str], quote_asset: str = "USDT") -> list[str]:
        """
        Convert a list of token symbols to Binance trading pair symbols.

        Example:
            [ETH, WETH, WBTC] -> [ETHUSDT, ETHUSDT, BTCUSDT]
        """
        return [SymbolConvertService.to_binance_symbol(symbol, quote_asset) for symbol in symbols]

    @staticmethod
    def remove_usdt_suffix(symbol: str) -> str:
        """
        Remove USDT suffix from a Binance trading pair symbol.

        Example:
            ETHUSDT -> ETH
            BTCUSDT -> BTC
            BNBUSDT -> BNB
        """
        if symbol == "USDT":
            return symbol
        if symbol and symbol.endswith("USDT"):
            return symbol[:-4]
        return symbol
    
    @staticmethod
    def remove_usdt_suffixes(symbols: list[str]) -> list[str]:
        """
        Remove USDT suffix from a list of Binance trading pair symbols.

        Example:
            [ETHUSDT, BTCUSDT, BNBUSDT] -> [ETH, BTC, BNB]
        """
        return [SymbolConvertService.remove_usdt_suffix(symbol) for symbol in symbols]