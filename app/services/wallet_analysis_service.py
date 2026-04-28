from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.models.wallet_models import (
    WalletAssetItem,
    WalletCategoryBreakdown,
    WalletChainOption,
    WalletGovernanceHint,
    WalletInsightResponse,
)
from app.services.asset_service import AssetService
from app.services.dashboard_tokens_service import DashboardTokensService
from app.services.price_service import PriceService
from app.services.symbol_mapper_service import SymbolConvertService
from app.storage.market_storage import MarketStorage
from app.utils.logging_config import get_logger


class WalletAnalysisServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class WalletAnalysisService:
    STABLECOIN_SYMBOLS = {"USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDP", "BUSD"}
    MAINSTREAM_SYMBOLS = {"BTC", "ETH", "BNB", "SOL", "ADA", "AVAX", "TON", "NEAR", "ARB", "OP"}
    DEFI_SYMBOLS = {"UNI", "AAVE", "LINK", "MKR", "COMP", "CRV", "SNX", "BAL", "YFI", "SUSHI"}
    MEME_SYMBOLS = {"DOGE", "SHIB", "PEPE", "FLOKI", "BONK"}

    CATEGORY_LABELS = {
        "store_of_value": "核心资产",
        "stablecoin": "稳定币",
        "native": "公链资产",
        "layer2": "Layer2",
        "defi": "DeFi",
        "oracle": "预言机",
        "storage": "存储",
        "meme": "Meme",
        "payments": "支付",
        "other": "其他",
    }

    def __init__(self) -> None:
        self.logger = get_logger("app.services.wallet_analysis_service")
        self.asset_service = AssetService()
        self.price_service = PriceService()
        self.storage = MarketStorage()
        self.dashboard_service = DashboardTokensService()
        self.wallet_config_path = Path(__file__).resolve().parents[2] / "configs" / "wallet_analysis_config.yaml"

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except Exception:
            return None

    def _load_wallet_config(self) -> dict[str, Any]:
        if not self.wallet_config_path.exists():
            raise WalletAnalysisServiceError(500, "WALLET_CONFIG_NOT_FOUND", "Wallet analysis config not found.")
        with self.wallet_config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}

    def _load_token_map(self) -> dict[str, dict[str, Any]]:
        cfg = self.dashboard_service.load_dashboard_config()
        return self.dashboard_service.token_map_from_config(cfg)

    def get_chain_options(self) -> list[WalletChainOption]:
        config = self._load_wallet_config()
        chains = config.get("supported_chains") or []
        options: list[WalletChainOption] = []
        for item in sorted(chains, key=lambda x: int(x.get("sort_order", 10**9)) if isinstance(x, dict) else 10**9):
            if not isinstance(item, dict) or not item.get("enabled", True):
                continue
            key = str(item.get("key", "")).strip()
            if not key:
                continue
            options.append(WalletChainOption(key=key, label=str(item.get("label") or key), enabled=True))
        return options

    def _safe_chains(self, chains: list[str]) -> list[str]:
        allowed = {item.key for item in self.get_chain_options()}
        selected = [str(chain).strip() for chain in chains if str(chain).strip()]
        if not selected:
            selected = list(allowed)
        safe = [chain for chain in selected if chain in allowed]
        if not safe:
            raise WalletAnalysisServiceError(400, "WALLET_CHAIN_INVALID", "No supported chain was selected.")
        return safe

    @staticmethod
    def _extract_assets(raw: dict[str, Any]) -> list[dict[str, Any]]:
        candidates = raw.get("assets") or raw.get("balance") or raw.get("blockchains") or []
        if isinstance(candidates, list):
            return [item for item in candidates if isinstance(item, dict)]
        if isinstance(candidates, dict):
            assets: list[dict[str, Any]] = []
            for value in candidates.values():
                if isinstance(value, list):
                    assets.extend(item for item in value if isinstance(item, dict))
            return assets
        return []

    def _cached_price(self, symbol: str) -> float | None:
        if symbol in self.STABLECOIN_SYMBOLS:
            return 1.0
        try:
            result = self.price_service.find_token_price(symbol)
            return self._as_float(result.get("price"))
        except Exception:
            return None

    def _normalize_asset(self, item: dict[str, Any], token_map: dict[str, dict[str, Any]]) -> WalletAssetItem | None:
        raw_symbol = str(item.get("tokenSymbol") or item.get("symbol") or "").strip()
        if not raw_symbol:
            return None
        try:
            symbol = SymbolConvertService.map_to_binance_base_symbol(raw_symbol)
        except Exception:
            symbol = raw_symbol.upper()

        token_cfg = token_map.get(symbol, {})
        balance = self._as_float(item.get("balance"))
        if balance is None:
            raw_balance = self._as_float(item.get("balanceRawInteger"))
            decimals = int(self._as_float(item.get("tokenDecimals")) or 0)
            if raw_balance is not None and decimals > 0:
                balance = raw_balance / (10**decimals)

        price = self._as_float(item.get("tokenPrice")) or self._cached_price(symbol)
        value = self._as_float(item.get("balanceUsd"))
        if value is None and balance is not None and price is not None:
            value = balance * price

        category = str(token_cfg.get("category") or "other")
        tags = token_cfg.get("tags") or []

        return WalletAssetItem(
            symbol=symbol,
            name=item.get("tokenName") or token_cfg.get("display_name") or token_cfg.get("name") or symbol,
            blockchain=item.get("blockchain"),
            token_type=item.get("tokenType"),
            contract_address=item.get("contractAddress"),
            balance=balance,
            display_balance=str(item.get("balance") or balance or "0"),
            price_usdt=price,
            value_usdt=max(0.0, float(value or 0)),
            category=category,
            logo=token_cfg.get("logo") or item.get("thumbnail"),
            tags=[str(tag) for tag in tags] if isinstance(tags, list) else [],
        )

    def _merge_assets(self, assets: list[WalletAssetItem]) -> list[WalletAssetItem]:
        merged: dict[tuple[str, str | None], WalletAssetItem] = {}
        for asset in assets:
            key = (asset.symbol, asset.blockchain)
            if key not in merged:
                merged[key] = asset
                continue
            current = merged[key]
            current.value_usdt += asset.value_usdt
            if current.balance is not None and asset.balance is not None:
                current.balance += asset.balance
                current.display_balance = f"{current.balance:.8f}".rstrip("0").rstrip(".")
        return sorted(merged.values(), key=lambda item: item.value_usdt, reverse=True)

    def _build_breakdown(self, assets: list[WalletAssetItem], total: float) -> list[WalletCategoryBreakdown]:
        bucket: dict[str, float] = {}
        for asset in assets:
            bucket[asset.category] = bucket.get(asset.category, 0.0) + asset.value_usdt
        return [
            WalletCategoryBreakdown(
                category=category,
                label=self.CATEGORY_LABELS.get(category, category),
                value_usdt=value,
                ratio=(value / total if total > 0 else 0),
            )
            for category, value in sorted(bucket.items(), key=lambda item: item[1], reverse=True)
            if value > 0
        ]

    def _sum_ratio(self, assets: list[WalletAssetItem], symbols: set[str], categories: set[str], total: float) -> float:
        if total <= 0:
            return 0
        value = sum(asset.value_usdt for asset in assets if asset.symbol in symbols or asset.category in categories)
        return value / total

    def _governance_hints(
        self,
        assets: list[WalletAssetItem],
        total: float,
        config: dict[str, Any],
    ) -> list[WalletGovernanceHint]:
        links = config.get("governance_token_links") or {}
        hints: list[WalletGovernanceHint] = []
        by_symbol: dict[str, float] = {}
        for asset in assets:
            by_symbol[asset.symbol] = by_symbol.get(asset.symbol, 0.0) + asset.value_usdt
        for symbol, value in sorted(by_symbol.items(), key=lambda item: item[1], reverse=True):
            link = links.get(symbol)
            if not isinstance(link, dict) or value <= 0:
                continue
            hints.append(
                WalletGovernanceHint(
                    symbol=symbol,
                    dao_name=str(link.get("dao_name") or symbol),
                    space_id=str(link.get("space_id") or ""),
                    value_usdt=value,
                    ratio=value / total if total > 0 else 0,
                )
            )
        return hints

    def _risk_level(self, concentration: float, stablecoin: float, meme: float) -> tuple[str, str]:
        if concentration >= 0.65 or meme >= 0.3:
            return "high", "较高"
        if concentration >= 0.45 or stablecoin < 0.12:
            return "medium", "中等"
        return "low", "较低"

    def _insights(
        self,
        assets: list[WalletAssetItem],
        total: float,
        stablecoin_ratio: float,
        defi_ratio: float,
        meme_ratio: float,
        governance_hints: list[WalletGovernanceHint],
        risk_label: str,
    ) -> list[str]:
        if total <= 0:
            return ["该地址在所选链上暂未发现可估值资产，建议确认地址和链选择是否正确。"]

        top = assets[0] if assets else None
        messages = [f"该地址当前估算总资产约 {total:,.2f} USDT，综合风险等级为{risk_label}。"]
        if top:
            messages.append(f"{top.symbol} 是当前占比最高的资产，占总资产约 {top.ratio * 100:.1f}%。")
        if stablecoin_ratio >= 0.35:
            messages.append(f"稳定币占比约 {stablecoin_ratio * 100:.1f}%，资产结构具有较强防御性。")
        elif stablecoin_ratio <= 0.08:
            messages.append("稳定币占比较低，组合对市场波动更敏感。")
        if defi_ratio >= 0.15:
            messages.append(f"DeFi/治理相关资产占比约 {defi_ratio * 100:.1f}%，可能关注协议治理和链上收益机会。")
        if meme_ratio >= 0.15:
            messages.append(f"Meme 资产占比约 {meme_ratio * 100:.1f}%，需要关注高波动风险。")
        if governance_hints:
            names = "、".join(hint.dao_name for hint in governance_hints[:3])
            messages.append(f"该地址持有治理相关代币，可进一步关注 {names} 的 DAO 提案。")
        return messages

    def analyze_wallet(self, address: str, chains: list[str]) -> WalletInsightResponse:
        wallet = (address or "").strip()
        if not wallet:
            raise WalletAnalysisServiceError(400, "WALLET_ADDRESS_REQUIRED", "Field 'address' is required.")

        safe_chains = self._safe_chains(chains)
        config = self._load_wallet_config()
        token_map = self._load_token_map()

        raw = self.asset_service.get_multichain_assets(wallet, safe_chains)
        normalized = [
            asset
            for asset in (self._normalize_asset(item, token_map) for item in self._extract_assets(raw))
            if asset is not None
        ]
        assets = self._merge_assets(normalized)
        total = sum(asset.value_usdt for asset in assets)
        priced_count = sum(1 for asset in assets if asset.price_usdt is not None or asset.value_usdt > 0)

        for asset in assets:
            asset.ratio = asset.value_usdt / total if total > 0 else 0

        stablecoin_ratio = self._sum_ratio(assets, self.STABLECOIN_SYMBOLS, {"stablecoin"}, total)
        mainstream_ratio = self._sum_ratio(assets, self.MAINSTREAM_SYMBOLS, {"store_of_value", "native", "layer2"}, total)
        defi_ratio = self._sum_ratio(assets, self.DEFI_SYMBOLS, {"defi", "oracle"}, total)
        meme_ratio = self._sum_ratio(assets, self.MEME_SYMBOLS, {"meme"}, total)
        concentration_ratio = assets[0].ratio if assets else 0
        governance_hints = self._governance_hints(assets, total, config)
        governance_ratio = sum(item.ratio for item in governance_hints)
        risk_level, risk_label = self._risk_level(concentration_ratio, stablecoin_ratio, meme_ratio)
        breakdown = self._build_breakdown(assets, total)

        response = WalletInsightResponse(
            address=wallet,
            chains=safe_chains,
            chain_options=self.get_chain_options(),
            asset_count=len(assets),
            priced_count=priced_count,
            total_value_usdt=total,
            stablecoin_ratio=stablecoin_ratio,
            mainstream_ratio=mainstream_ratio,
            defi_ratio=defi_ratio,
            meme_ratio=meme_ratio,
            governance_ratio=governance_ratio,
            concentration_ratio=concentration_ratio,
            risk_level=risk_level,
            risk_label=risk_label,
            page_updated_at=self._utc_now_iso(),
            assets=assets,
            category_breakdown=breakdown,
            governance_hints=governance_hints,
            insights=self._insights(assets, total, stablecoin_ratio, defi_ratio, meme_ratio, governance_hints, risk_label),
        )

        try:
            payload = response.model_dump() if hasattr(response, "model_dump") else response.dict()
            self.storage.save_asset_overview(wallet, safe_chains, payload)
        except Exception:
            self.logger.exception("Failed to store wallet analysis address=%s chains=%s", wallet, safe_chains)

        return response
