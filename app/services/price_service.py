from app.clients.binance_client import BinanceClient


class PriceService:
    def __init__(self) -> None:
        self.client = BinanceClient()

    def get_symbol_price(self, symbol: str) -> dict:
        return self.client.get_symbol_price(symbol)

    def get_symbols_price(self, symbols: list[str]) -> list[dict]:
        return self.client.get_multi_symbol_price(symbols)