from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from fastapi import HTTPException, status

from app.models.dashboard_tokens import (
    TokenCard,
    TokenGroup,
    TokenOverviewResponse,
    TokenRefreshAllResponse,
    TokenRefreshGroup,
)
from app.services.chain_rpc_service import ChainRPCService
from app.services.price_service import PriceService
from app.services.symbol_mapper_service import SymbolConvertService
from app.utils.logging_config import get_logger


class DashboardTokensService:
    """Service layer for dashboard tokens overview/refresh endpoints."""

    def __init__(self) -> None:
        self.logger = get_logger("app.services.dashboard_tokens_service")
        self.chain_rpc_service = ChainRPCService()
        self.price_service = PriceService()
        self.config_path = Path(__file__).resolve().parents[2] / "configs" / "dashboard_tokens_config.yaml"

    @staticmethod
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def to_iso_utc(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return str(value)

    def load_dashboard_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "DASHBOARD_OVERVIEW_ERROR",
                    "message": f"Config not found: {self.config_path}",
                },
            )
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            if not isinstance(config, dict):
                raise ValueError("dashboard config root must be an object")
            return config
        except HTTPException:
            raise
        except Exception as exc:
            self.logger.exception("Failed to load dashboard tokens config")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "DASHBOARD_OVERVIEW_ERROR",
                    "message": f"Failed to load dashboard token config: {exc}",
                },
            ) from exc

    def fetch_price_from_mongo(self, symbol: str) -> tuple[float | None, str | None]:
        try:
            result = self.price_service.find_token_price(symbol)
            price = result.get("price")
            updated_at = self.to_iso_utc(result.get("updated_at"))
            return (float(price) if price is not None else None), updated_at
        except Exception:
            self.logger.warning("Mongo price lookup failed symbol=%s", symbol)
            return None, None

    def check_rpc_status(self, chain: str | None) -> bool:
        if not chain:
            return False
        try:
            health = self.chain_rpc_service.get_chain_health(chain)
            return bool(health.get("connected"))
        except Exception:
            self.logger.warning("RPC health check failed chain=%s", chain)
            return False

    @staticmethod
    def build_status(rpc_ok: bool, price: float | None) -> str:
        if rpc_ok and price is not None:
            return "online"
        if rpc_ok or price is not None:
            return "partial"
        return "unavailable"

    def build_token_card_with_dynamic(
        self,
        token_cfg: dict[str, Any],
        price: float | None,
        updated_at: str | None,
    ) -> TokenCard:
        symbol = str(token_cfg.get("symbol", "")).upper()
        name = str(token_cfg.get("name", symbol))
        display_name = str(token_cfg.get("display_name", name))
        primary_chain = str(token_cfg.get("primary_chain", ""))
        category = str(token_cfg.get("category", ""))
        logo = str(token_cfg.get("logo", ""))
        tags = token_cfg.get("tags") or []
        tags = [str(tag) for tag in tags] if isinstance(tags, list) else []

        rpc_ok = self.check_rpc_status(primary_chain)
        status_value = self.build_status(rpc_ok=rpc_ok, price=price)
        price_display = "--" if price is None else f"{price:.2f} USDT"

        return TokenCard(
            symbol=symbol,
            name=name,
            display_name=display_name,
            primary_chain=primary_chain,
            category=category,
            logo=logo,
            price=price,
            price_display=price_display,
            updated_at=updated_at,
            status=status_value,
            tags=tags,
        )

    def build_overview_card(self, token_cfg: dict[str, Any]) -> TokenCard:
        symbol = str(token_cfg.get("symbol", "")).upper()
        name = str(token_cfg.get("name", symbol))
        display_name = str(token_cfg.get("display_name", name))
        primary_chain = str(token_cfg.get("primary_chain", ""))
        category = str(token_cfg.get("category", ""))
        logo = str(token_cfg.get("logo", ""))
        tags = token_cfg.get("tags") or []
        tags = [str(tag) for tag in tags] if isinstance(tags, list) else []

        price, updated_at = self.fetch_price_from_mongo(symbol)
        rpc_ok = self.check_rpc_status(primary_chain)
        status_value = self.build_status(rpc_ok=rpc_ok, price=price)
        price_display = "--" if price is None else f"{price:.2f} USDT"

        return TokenCard(
            symbol=symbol,
            name=name,
            display_name=display_name,
            primary_chain=primary_chain,
            category=category,
            logo=logo,
            price=price,
            price_display=price_display,
            updated_at=updated_at,
            status=status_value,
            tags=tags,
        )

    @staticmethod
    def normalize_compact_symbol(symbol: str | None) -> str:
        raw = str(symbol or "").upper()
        if not raw:
            return raw
        base = SymbolConvertService.remove_usdt_suffix(raw)
        return SymbolConvertService.map_to_binance_base_symbol(base)

    def compact_price_map(self, compact_prices: list[dict[str, Any]]) -> dict[str, float]:
        result: dict[str, float] = {}
        for item in compact_prices:
            if not isinstance(item, dict):
                continue
            base_symbol = self.normalize_compact_symbol(item.get("symbol"))
            if not base_symbol:
                continue
            price_raw = item.get("price")
            if price_raw is None:
                continue
            try:
                result[base_symbol] = float(price_raw)
            except Exception:
                continue
        return result

    @staticmethod
    def token_map_from_config(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
        tokens = config.get("dashboard_tokens") or []
        token_map: dict[str, dict[str, Any]] = {}
        if not isinstance(tokens, list):
            return token_map
        for token in tokens:
            if not isinstance(token, dict):
                continue
            if not token.get("enabled", True):
                continue
            if not token.get("show_on_dashboard", True):
                continue
            symbol = str(token.get("symbol", "")).upper()
            if not symbol:
                continue
            token_map[symbol] = token
        return token_map

    def get_overview(self) -> TokenOverviewResponse:
        config = self.load_dashboard_config()
        token_map = self.token_map_from_config(config)
        groups = config.get("dashboard_groups") or []

        payload_groups: list[TokenGroup] = []
        total_tokens = 0

        if isinstance(groups, list):
            for group in groups:
                if not isinstance(group, dict):
                    continue
                group_name = str(group.get("group_name", ""))
                group_key = str(group.get("group_key", ""))
                symbols = group.get("symbols") or []

                cards: list[TokenCard] = []
                if isinstance(symbols, list):
                    for symbol in symbols:
                        symbol_key = str(symbol).upper()
                        token_cfg = token_map.get(symbol_key)
                        if not token_cfg:
                            continue
                        cards.append(self.build_overview_card(token_cfg))

                total_tokens += len(cards)
                payload_groups.append(TokenGroup(group_name=group_name, group_key=group_key, cards=cards))

        return TokenOverviewResponse(
            page_updated_at=self.utc_now_iso(),
            total_tokens=total_tokens,
            group_count=len(payload_groups),
            groups=payload_groups,
        )

    def refresh_all(self) -> TokenRefreshAllResponse:
        config = self.load_dashboard_config()
        token_map = self.token_map_from_config(config)
        groups = config.get("dashboard_groups") or []
        all_symbols = list(token_map.keys())
        _, compact_prices = self.price_service.update_get_binance_tokens_price_tuple(all_symbols)
        price_map = self.compact_price_map(compact_prices)
        refreshed_at = self.utc_now_iso()

        payload_groups: list[TokenRefreshGroup] = []
        total_tokens = 0

        if isinstance(groups, list):
            for group in groups:
                if not isinstance(group, dict):
                    continue

                group_name = str(group.get("group_name", ""))
                group_key = str(group.get("group_key", ""))
                symbols = group.get("symbols") or []

                cards: list[TokenCard] = []
                if isinstance(symbols, list):
                    for symbol in symbols:
                        symbol_key = str(symbol).upper()
                        token_cfg = token_map.get(symbol_key)
                        if not token_cfg:
                            continue
                        cards.append(
                            self.build_token_card_with_dynamic(
                                token_cfg,
                                price=price_map.get(symbol_key),
                                updated_at=refreshed_at,
                            )
                        )

                total_tokens += len(cards)
                payload_groups.append(TokenRefreshGroup(group_name=group_name, group_key=group_key, cards=cards))

        return TokenRefreshAllResponse(
            page_updated_at=self.utc_now_iso(),
            total_tokens=total_tokens,
            group_count=len(payload_groups),
            groups=payload_groups,
        )

    def refresh_one(self, symbol: str) -> TokenCard:
        symbol = (symbol or "").strip().upper()
        config = self.load_dashboard_config()
        token_map = self.token_map_from_config(config)
        token_cfg = token_map.get(symbol)
        if token_cfg is None:
            raise LookupError("TOKEN_NOT_FOUND")

        self.logger.info("Refreshing dashboard token card symbol=%s", symbol)
        _, compact_price = self.price_service.update_get_binance_token_price_tuple(symbol)
        price_map = self.compact_price_map([compact_price])
        refreshed_at = self.utc_now_iso()
        return self.build_token_card_with_dynamic(
            token_cfg,
            price=price_map.get(symbol),
            updated_at=refreshed_at,
        )

