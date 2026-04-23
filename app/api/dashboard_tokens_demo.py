from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.chain_rpc_service import ChainRPCService
from app.services.price_service import PriceService
from app.services.symbol_mapper_service import SymbolConvertService
from app.utils.logging_config import get_logger


logger = get_logger("app.api.dashboard_tokens_demo")
router = APIRouter(prefix="/api/dashboard/tokens", tags=["dashboard-tokens"])

_ROOT_DIR = Path(__file__).resolve().parents[2]
_TOKENS_CONFIG_PATH = _ROOT_DIR / "configs" / "dashboard_tokens_config.yaml"

_chain_rpc_service = ChainRPCService()
_price_service = PriceService()


class ErrorResponse(BaseModel):
    code: str
    message: str


class TokenCard(BaseModel):
    symbol: str
    name: str
    display_name: str
    primary_chain: str
    category: str
    logo: str
    price: float | None
    price_display: str
    updated_at: str | None
    status: str
    tags: list[str] = Field(default_factory=list)


class TokenGroup(BaseModel):
    group_name: str
    group_key: str
    cards: list[TokenCard] = Field(default_factory=list)


class TokenOverviewResponse(BaseModel):
    page_updated_at: str
    total_tokens: int
    group_count: int
    groups: list[TokenGroup] = Field(default_factory=list)


class TokenRefreshRequest(BaseModel):
    symbol: str = Field(..., description="Token symbol to refresh, e.g. ETH")


class TokenRefreshGroup(BaseModel):
    group_name: str
    group_key: str
    cards: list[TokenCard] = Field(default_factory=list)


class TokenRefreshAllResponse(BaseModel):
    page_updated_at: str
    total_tokens: int
    group_count: int
    groups: list[TokenRefreshGroup] = Field(default_factory=list)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _to_iso_utc(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)


def _load_dashboard_config() -> dict[str, Any]:
    if not _TOKENS_CONFIG_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DASHBOARD_OVERVIEW_ERROR",
                "message": f"Config not found: {_TOKENS_CONFIG_PATH}",
            },
        )

    try:
        with _TOKENS_CONFIG_PATH.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config, dict):
            raise ValueError("dashboard config root must be an object")
        return config
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to load dashboard tokens config")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DASHBOARD_OVERVIEW_ERROR",
                "message": f"Failed to load dashboard token config: {exc}",
            },
        ) from exc


def _fetch_price_from_mongo(symbol: str) -> tuple[float | None, str | None]:
    try:
        result = _price_service.find_token_price(symbol)
        price = result.get("price")
        updated_at = _to_iso_utc(result.get("updated_at"))
        return (float(price) if price is not None else None), updated_at
    except Exception:
        logger.warning("Mongo price lookup failed symbol=%s", symbol)
        return None, None


def _check_rpc_status(chain: str | None) -> tuple[bool, str]:
    if not chain:
        return False, "rpc"
    try:
        health = _chain_rpc_service.get_chain_health(chain)
        return bool(health.get("connected")), "rpc"
    except Exception:
        logger.warning("RPC health check failed chain=%s", chain)
        return False, "rpc"


def _build_status(rpc_ok: bool, price: float | None) -> str:
    if rpc_ok and price is not None:
        return "online"
    if rpc_ok or price is not None:
        return "partial"
    return "unavailable"


def _build_token_card_with_dynamic(
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

    rpc_ok, _ = _check_rpc_status(primary_chain)
    status_value = _build_status(rpc_ok=rpc_ok, price=price)
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


def _build_overview_card(token_cfg: dict[str, Any]) -> TokenCard:
    symbol = str(token_cfg.get("symbol", "")).upper()
    name = str(token_cfg.get("name", symbol))
    display_name = str(token_cfg.get("display_name", name))
    primary_chain = str(token_cfg.get("primary_chain", ""))
    category = str(token_cfg.get("category", ""))
    logo = str(token_cfg.get("logo", ""))
    tags = token_cfg.get("tags") or []
    tags = [str(tag) for tag in tags] if isinstance(tags, list) else []

    # Overview price/updated_at come from MongoDB token_prices_collection.
    price, updated_at = _fetch_price_from_mongo(symbol)
    rpc_ok, _ = _check_rpc_status(primary_chain)
    status_value = _build_status(rpc_ok=rpc_ok, price=price)
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


def _normalize_compact_symbol(symbol: str | None) -> str:
    raw = str(symbol or "").upper()
    if not raw:
        return raw
    base = SymbolConvertService.remove_usdt_suffix(raw)
    return SymbolConvertService.map_to_binance_base_symbol(base)


def _compact_price_map(compact_prices: list[dict[str, Any]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for item in compact_prices:
        if not isinstance(item, dict):
            continue
        base_symbol = _normalize_compact_symbol(item.get("symbol"))
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


def _token_map_from_config(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
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


def _build_refresh_all_payload(config: dict[str, Any]) -> TokenRefreshAllResponse:
    token_map = _token_map_from_config(config)
    groups = config.get("dashboard_groups") or []
    all_symbols = list(token_map.keys())
    _, compact_prices = _price_service.update_get_binance_tokens_price_tuple(all_symbols)
    price_map = _compact_price_map(compact_prices)
    refreshed_at = _utc_now_iso()

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
                    price = price_map.get(symbol_key)
                    cards.append(_build_token_card_with_dynamic(token_cfg, price=price, updated_at=refreshed_at))

            total_tokens += len(cards)
            payload_groups.append(
                TokenRefreshGroup(
                    group_name=group_name,
                    group_key=group_key,
                    cards=cards,
                )
            )

    return TokenRefreshAllResponse(
        page_updated_at=_utc_now_iso(),
        total_tokens=total_tokens,
        group_count=len(payload_groups),
        groups=payload_groups,
    )


@router.get(
    "/overview",
    response_model=TokenOverviewResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_dashboard_tokens_overview() -> TokenOverviewResponse:
    try:
        config = _load_dashboard_config()
        token_map = _token_map_from_config(config)
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
                        card = _build_overview_card(token_cfg)
                        cards.append(card)

                total_tokens += len(cards)
                payload_groups.append(
                    TokenGroup(
                        group_name=group_name,
                        group_key=group_key,
                        cards=cards,
                    )
                )

        return TokenOverviewResponse(
            page_updated_at=_utc_now_iso(),
            total_tokens=total_tokens,
            group_count=len(payload_groups),
            groups=payload_groups,
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": "DASHBOARD_OVERVIEW_ERROR", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=detail)
    except Exception:
        logger.exception("Unexpected error in dashboard overview endpoint")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"code": "DASHBOARD_OVERVIEW_ERROR", "message": "Failed to load dashboard token overview."},
        )


@router.post(
    "/refresh/all",
    response_model=TokenRefreshAllResponse,
    responses={500: {"model": ErrorResponse}},
)
def refresh_all_dashboard_tokens() -> TokenRefreshAllResponse:
    try:
        config = _load_dashboard_config()
        return _build_refresh_all_payload(config)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": "DASHBOARD_REFRESH_ALL_ERROR", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=detail)
    except Exception:
        logger.exception("Unexpected error in dashboard refresh-all endpoint")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"code": "DASHBOARD_REFRESH_ALL_ERROR", "message": "Failed to refresh all dashboard token cards."},
        )


@router.post(
    "/refresh",
    response_model=TokenCard,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def refresh_dashboard_token_card(req: TokenRefreshRequest) -> TokenCard:
    try:
        symbol = req.symbol.strip().upper() if req.symbol else ""
        if not symbol:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"code": "SYMBOL_REQUIRED", "message": "Field 'symbol' is required."},
            )

        config = _load_dashboard_config()
        token_map = _token_map_from_config(config)
        token_cfg = token_map.get(symbol)
        if token_cfg is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"code": "TOKEN_NOT_FOUND", "message": "Token configuration not found."},
            )

        _, compact_price = _price_service.update_get_binance_token_price_tuple(symbol)
        price_map = _compact_price_map([compact_price])
        refreshed_at = _utc_now_iso()
        return _build_token_card_with_dynamic(
            token_cfg,
            price=price_map.get(symbol),
            updated_at=refreshed_at,
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": "DASHBOARD_REFRESH_ERROR", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=detail)
    except Exception:
        logger.exception("Unexpected error in dashboard refresh endpoint")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"code": "DASHBOARD_REFRESH_ERROR", "message": "Failed to refresh dashboard token card."},
        )
