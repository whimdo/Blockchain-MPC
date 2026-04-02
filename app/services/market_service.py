from __future__ import annotations

from app.services.asset_service import AssetService
from app.services.price_service import PriceService
from app.utils.logging_config import get_logger


class MarketService:
    """Service to aggregate wallet assets and market prices."""

    def __init__(self) -> None:
        """Initialize market aggregation service."""
        self.logger = get_logger("app.services.market_service")
        self.asset_service = AssetService()
        self.price_service = PriceService()

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

            normalized_assets = []
            if isinstance(assets, list):
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
                if symbol and symbol not in {"USDT", "USDC", "BUSD"}:
                    symbols_to_query.append(f"{symbol}USDT")

            symbols_to_query = list(dict.fromkeys(symbols_to_query))
            prices = self.price_service.get_symbols_price(symbols_to_query) if symbols_to_query else []
            price_map = {item["symbol"]: item["price"] for item in prices if "symbol" in item}

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
            self.logger.info(
                "Wallet aggregation completed address=%s asset_count=%s",
                address,
                result["asset_count"],
            )
            return result
        except Exception:
            self.logger.exception("Wallet aggregation failed address=%s chains=%s", address, chains)
            raise
