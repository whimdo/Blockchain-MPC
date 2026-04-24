from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.clients.multichain_client import MultiChainClient
from app.clients.token_detail_market_client import TokenDetailMarketClient
from app.services.price_service import PriceService
from app.utils.logging_config import get_logger


class TokenDetailDemoService:
    """Aggregate token detail data for detail/chart/refresh demo APIs."""

    RANGE_TO_INTERVAL: dict[str, str] = {
        "1d": "15m",
        "7d": "1h",
        "1m": "4h",
        "3m": "1d",
        "1y": "1d",
    }

    RANGE_TO_LIMIT: dict[str, int] = {
        "1d": 96,
        "7d": 168,
        "1m": 180,
        "3m": 90,
        "1y": 365,
    }

    SUPPORTED_INTERVALS = {"15m", "1h", "4h", "1d", "1w"}

    EVM_CHAINS = {"ethereum", "bsc", "polygon"}

    def __init__(self) -> None:
        self.logger = get_logger("app.services.token_detail_demo_service")
        self.price_service = PriceService()
        self.market_client = TokenDetailMarketClient()
        self.rpc_client = MultiChainClient()
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

    @staticmethod
    def as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def format_price_display(price: float | None) -> str:
        if price is None:
            return "--"
        return f"{price:.2f} USDT"

    def load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        with self.config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError("dashboard token config root must be object")
        return data

    def get_token_config(self, symbol: str) -> dict[str, Any] | None:
        cfg = self.load_config()
        tokens = cfg.get("dashboard_tokens") or []
        symbol = (symbol or "").upper()

        if not isinstance(tokens, list):
            return None

        for token in tokens:
            if not isinstance(token, dict):
                continue
            token_symbol = str(token.get("symbol", "")).upper()
            if token_symbol != symbol:
                continue
            if not token.get("enabled", True):
                return None
            return token
        return None

    def build_market_status(self, token_cfg: dict[str, Any], force_refresh: bool = False) -> dict[str, Any]:
        symbol = str(token_cfg.get("symbol", "")).upper()
        pair = str(token_cfg.get("price_symbol", "") or f"{symbol}USDT").upper()

        source = "none"
        price = None
        price_change_24h = None
        high_24h = None
        low_24h = None
        volume_24h = None
        updated_at = self.utc_now_iso()

        try:
            if force_refresh:
                _, compact = self.price_service.update_get_binance_token_price_tuple(symbol)
                price = self.as_float(compact.get("price"))
                source = "binance"
            else:
                mongo_price = self.price_service.find_token_price(symbol)
                price = self.as_float(mongo_price.get("price"))
                updated_at = self.to_iso_utc(mongo_price.get("updated_at")) or updated_at
                if price is not None:
                    source = "mongo"
        except Exception:
            self.logger.warning("Price lookup failed symbol=%s", symbol)

        try:
            ticker_24h = self.market_client.get_24hr_ticker(pair)
            if price is None:
                price = self.as_float(ticker_24h.get("lastPrice"))
            price_change_24h = self.as_float(ticker_24h.get("priceChangePercent"))
            high_24h = self.as_float(ticker_24h.get("highPrice"))
            low_24h = self.as_float(ticker_24h.get("lowPrice"))
            volume_24h = self.as_float(ticker_24h.get("quoteVolume"))
            source = "binance"
            updated_at = self.utc_now_iso()
        except Exception:
            self.logger.warning("24hr ticker failed pair=%s", pair)

        return {
            "price": price,
            "price_display": self.format_price_display(price),
            "price_change_24h": price_change_24h,
            "high_24h": high_24h,
            "low_24h": low_24h,
            "volume_24h": volume_24h,
            "source": source,
            "updated_at": updated_at,
        }

    def build_chain_status(self, token_cfg: dict[str, Any], force_refresh: bool = False) -> dict[str, Any]:
        _ = force_refresh
        chain = str(token_cfg.get("primary_chain", "")).lower()
        checked_at = self.utc_now_iso()

        if chain not in self.EVM_CHAINS:
            return {
                "primary_chain": chain,
                "chain_supported": False,
                "rpc_status": "unsupported",
                "latest_block": None,
                "gas_price": None,
                "last_checked_at": checked_at,
                "onchain_data_status": "not_integrated",
            }

        try:
            connected = self.rpc_client.is_connected(chain)
            if not connected:
                return {
                    "primary_chain": chain,
                    "chain_supported": True,
                    "rpc_status": "offline",
                    "latest_block": None,
                    "gas_price": None,
                    "last_checked_at": checked_at,
                    "onchain_data_status": "unavailable",
                }

            latest_block = self.rpc_client.get_latest_block_number(chain)
            gas_price_wei = self.rpc_client.get_client(chain).eth.gas_price
            gas_gwei = round(gas_price_wei / 1_000_000_000, 4)

            return {
                "primary_chain": chain,
                "chain_supported": True,
                "rpc_status": "online",
                "latest_block": latest_block,
                "gas_price": f"{gas_gwei} gwei",
                "last_checked_at": checked_at,
                "onchain_data_status": "available",
            }
        except Exception:
            self.logger.warning("Chain status lookup failed chain=%s", chain)
            return {
                "primary_chain": chain,
                "chain_supported": True,
                "rpc_status": "error",
                "latest_block": None,
                "gas_price": None,
                "last_checked_at": checked_at,
                "onchain_data_status": "unavailable",
            }

    def build_overview(self, token_cfg: dict[str, Any], market_status: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": str(token_cfg.get("symbol", "")).upper(),
            "name": str(token_cfg.get("name", "")),
            "display_name": str(token_cfg.get("display_name", "")),
            "logo": str(token_cfg.get("logo", "")),
            "primary_chain": str(token_cfg.get("primary_chain", "")).lower(),
            "category": str(token_cfg.get("category", "")),
            "tags": token_cfg.get("tags") or [],
            "price_display": market_status.get("price_display"),
            "updated_at": market_status.get("updated_at"),
            "status": "online" if market_status.get("source") != "none" else "unavailable",
        }

    def build_basic_info(self, token_cfg: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": str(token_cfg.get("symbol", "")).upper(),
            "name": str(token_cfg.get("name", "")),
            "display_name": str(token_cfg.get("display_name", "")),
            "primary_chain": str(token_cfg.get("primary_chain", "")).lower(),
            "category": str(token_cfg.get("category", "")),
            "price_symbol": str(token_cfg.get("price_symbol", "")),
            "description": str(token_cfg.get("description", "")),
            "tags": token_cfg.get("tags") or [],
        }

    def build_ai_summary(
        self,
        token_cfg: dict[str, Any],
        market_status: dict[str, Any],
        chain_status: dict[str, Any],
    ) -> dict[str, Any]:
        now = self.utc_now_iso()
        summary = (
            f"{token_cfg.get('display_name')} 是一个 {token_cfg.get('category')} 类型的加密资产，"
            f"主链为 {token_cfg.get('primary_chain')}。"
            f"当前价格为 {market_status.get('price_display')}，24h 涨跌幅为 {market_status.get('price_change_24h')}%。"
            f"链上状态为 {chain_status.get('rpc_status')}，最近检查时间 {chain_status.get('last_checked_at')}。"
        )
        return {
            "summary": summary,
            "generated_by": "template",
            "generated_at": now,
        }

    def build_detail(self, symbol: str) -> dict[str, Any]:
        token_cfg = self.get_token_config(symbol)
        if token_cfg is None:
            raise LookupError("TOKEN_NOT_FOUND")

        market_status = self.build_market_status(token_cfg, force_refresh=False)
        chain_status = self.build_chain_status(token_cfg, force_refresh=False)

        return {
            "symbol": str(token_cfg.get("symbol", "")).upper(),
            "overview": self.build_overview(token_cfg, market_status),
            "basic_info": self.build_basic_info(token_cfg),
            "market_status": market_status,
            "chain_status": chain_status,
            "ai_summary": self.build_ai_summary(token_cfg, market_status, chain_status),
        }

    def build_chart(self, symbol: str, chart_range: str, interval: str | None = None) -> dict[str, Any]:
        token_cfg = self.get_token_config(symbol)
        if token_cfg is None:
            raise LookupError("TOKEN_NOT_FOUND")

        symbol = str(token_cfg.get("symbol", "")).upper()
        pair = str(token_cfg.get("price_symbol", "") or f"{symbol}USDT").upper()

        chart_range = (chart_range or "7d").lower()
        if chart_range not in self.RANGE_TO_INTERVAL:
            chart_range = "7d"

        use_interval = (interval or self.RANGE_TO_INTERVAL[chart_range]).lower()
        if use_interval not in self.SUPPORTED_INTERVALS:
            use_interval = self.RANGE_TO_INTERVAL[chart_range]

        limit = self.RANGE_TO_LIMIT.get(chart_range, 168)

        try:
            klines = self.market_client.get_klines(pair, use_interval, limit)
            price_points: list[dict[str, Any]] = []
            volume_points: list[dict[str, Any]] = []

            for item in klines:
                if not isinstance(item, list) or len(item) < 11:
                    continue

                open_time = int(item[0])
                timestamp = datetime.fromtimestamp(open_time / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")

                price_points.append(
                    {
                        "timestamp": timestamp,
                        "open": self.as_float(item[1]),
                        "high": self.as_float(item[2]),
                        "low": self.as_float(item[3]),
                        "close": self.as_float(item[4]),
                    }
                )

                volume_points.append(
                    {
                        "timestamp": timestamp,
                        "volume": self.as_float(item[5]),
                        "quote_volume": self.as_float(item[7]),
                        "trades_count": int(item[8]) if str(item[8]).isdigit() else None,
                    }
                )

            return {
                "symbol": symbol,
                "range": chart_range,
                "interval": use_interval,
                "source": "binance",
                "price_points": price_points,
                "volume_points": volume_points,
            }
        except Exception:
            self.logger.warning("Chart lookup failed symbol=%s pair=%s", symbol, pair)
            return {
                "symbol": symbol,
                "range": chart_range,
                "interval": use_interval,
                "source": "none",
                "price_points": [],
                "volume_points": [],
                "message": "Chart data is currently unavailable.",
            }

    def build_refresh(self, symbol: str) -> dict[str, Any]:
        token_cfg = self.get_token_config(symbol)
        if token_cfg is None:
            raise LookupError("TOKEN_NOT_FOUND")

        market_status = self.build_market_status(token_cfg, force_refresh=True)
        chain_status = self.build_chain_status(token_cfg, force_refresh=True)

        return {
            "symbol": str(token_cfg.get("symbol", "")).upper(),
            "market_status": market_status,
            "chain_status": chain_status,
            "updated_at": self.utc_now_iso(),
        }
