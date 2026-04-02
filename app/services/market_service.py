from __future__ import annotations

from app.services.asset_service import AssetService
from app.services.price_service import PriceService


class MarketService:
    """
    多链资产 + Binance价格 聚合服务
    """

    def __init__(self) -> None:
        self.asset_service = AssetService()
        self.price_service = PriceService()

    def get_wallet_assets_with_prices(self, address: str, chains: list[str]) -> dict:
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
            for _, value in assets.items():
                if isinstance(value, list):
                    normalized_assets.extend(value)

        symbols_to_query = []
        for item in normalized_assets:
            symbol = (item.get("tokenSymbol") or item.get("symbol") or "").upper()
            if symbol and symbol not in {"USDT", "USDC", "BUSD"}:
                symbols_to_query.append(f"{symbol}USDT")

        symbols_to_query = list(dict.fromkeys(symbols_to_query))
        prices = self.price_service.get_symbols_price(symbols_to_query) if symbols_to_query else []
        price_map = {item["symbol"]: item["price"] for item in prices}

        enriched_assets = []
        for item in normalized_assets:
            symbol = (item.get("tokenSymbol") or item.get("symbol") or "").upper()
            pair = f"{symbol}USDT" if symbol else None
            balance = item.get("balance") or item.get("balanceRawInteger") or None

            enriched_assets.append({
                **item,
                "binance_symbol": pair if pair in price_map else None,
                "market_price_usdt": price_map.get(pair) if pair else None,
                "estimated_value_usdt": None,  # 后面可以再精细计算
                "display_balance": balance,
            })

        return {
            "address": address,
            "chains": chains,
            "asset_count": len(enriched_assets),
            "assets": enriched_assets,
        }