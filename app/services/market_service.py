from __future__ import annotations

from app.services.asset_service import AssetService
from app.services.price_service import PriceService
from app.storage.market_storage import MarketStorage
from app.services.symbol_mapper_service import SymbolConvertService
from app.utils.logging_config import get_logger


class MarketService:
    """Service to aggregate wallet assets and market prices."""

    def __init__(self) -> None:
        """Initialize market aggregation service."""
        self.logger = get_logger("app.services.market_service")
        self.asset_service = AssetService()
        self.price_service = PriceService()
        self.storage = MarketStorage()

    def get_wallet_assets_with_prices(self, address: str, chains: list[str]) -> dict:
        """Aggregate wallet assets and enrich with Binance prices."""
        try:
            self.logger.info("Starting wallet aggregation address=%s chains=%s", address, chains)
            asset_result = self.asset_service.get_multichain_assets(address, chains)

            assets = (
                asset_result.get("assets")
                or asset_result.get("balance")
                or asset_result.get("blockchains")
                or []
            )

            for item in assets:
                symbol = (item.get("tokenSymbol") or item.get("symbol") or "").upper()
                if not symbol or not str(symbol).strip():
                    self.logger.warning("Skipping asset with missing symbol: %s", item)
                    continue
                symbol = SymbolConvertService.map_to_binance_base_symbol(symbol)
                price = item.get("tokenPrice")
                try:
                    id = self.price_service.update_get_ankr_token_price(symbol,price)
                    self.logger.info("Fetched price for symbol=%s from Ankr price update id=%s", symbol, id)
                except Exception:
                    self.logger.exception("Failed to fetch price for symbol=%s", symbol)
                    price = None

            normalized_assets = []
            if isinstance(assets, list):
                self.logger.info("Assets is a list with length: %d", len(assets))
                for item in assets:
                    if isinstance(item, dict):
                        normalized_assets.append(item)
            elif isinstance(assets, dict):
                for value in assets.values():
                    if isinstance(value, list):
                        normalized_assets.extend(value)

            symbols_to_query = []
            for item in normalized_assets:
                symbol = (item.get("tokenSymbol") or item.get("symbol") or "").upper()
                if not symbol or not str(symbol).strip():
                    self.logger.warning("Skipping asset with missing symbol: %s", item)
                    continue 
                symbol = SymbolConvertService.to_binance_symbol(symbol)
                symbols_to_query.append(symbol)

            # for item in symbols_to_query:
            #     self.logger.info("Prepared symbol for price query: %s", item)
            #     price = PriceService().get_symbol_price(item)
            #     id = self.price_service.update_get_binance_token_price(item, price.get("price"))
            #     self.logger.info("Updated price for symbol=%s with id=%s", item, id)

            def chunk_list(lst, size):
                for i in range(0, len(lst), size):
                    yield lst[i:i + size]

            symbols_to_query = list(dict.fromkeys(symbols_to_query))

            all_prices = []

            for chunk in chunk_list(symbols_to_query, 20):
                try:
                    prices = self.price_service.get_symbols_price(chunk)
                    all_prices.extend(prices)
                except Exception as e:
                    print("Chunk failed:", chunk, e)

            for price in all_prices:
                self.logger.info("Fetched price: symbol=%s price=%s", price.get("symbol"), price.get("price"))
                id = self.price_service.update_get_binance_token_price(SymbolConvertService.remove_usdt_suffix(price.get("symbol")), price.get("price"))
                self.logger.info("Updated price for symbol=%s with id=%s", price.get("symbol"), id)

            price_map = {p["symbol"]: p["price"] for p in all_prices}
            enriched_assets = []
            for item in normalized_assets:
                symbol = (item.get("tokenSymbol") or item.get("symbol") or "").upper()
                pair = f"{symbol}USDT" if symbol else None
                balance = item.get("balance") or item.get("balanceRawInteger")
                enriched_assets.append(
                    {
                        **item,
                        "binance_symbol": pair if pair in price_map else None,
                        "market_price_usdt": price_map.get(pair) if pair else None,
                        "estimated_value_usdt": None,
                        "display_balance": balance,
                    }
                )

            result = {
                "address": address,
                "chains": chains,
                "asset_count": len(enriched_assets),
                "assets": enriched_assets,
            }
            try:
                inserted_id = self.storage.save_asset_overview(address, chains, result)
                self.logger.info("Stored wallet overview inserted_id=%s", inserted_id)
            except Exception:
                self.logger.exception(
                    "Failed to store wallet overview address=%s chains=%s",
                    address,
                    chains,
                )
            self.logger.info(
                "Wallet aggregation completed address=%s asset_count=%s",
                address,
                result["asset_count"],
            )
            return result
        except Exception:
            self.logger.exception("Wallet aggregation failed address=%s chains=%s", address, chains)
            raise
