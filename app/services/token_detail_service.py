from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.clients.binance_client import BinanceClient
from app.models.token_detail_models import (
    TokenChartKlinePoint,
    TokenChartResponse,
    TokenChartSummary,
    TokenDetailResponse,
    TokenInfoBlock,
)
from app.services.price_service import PriceService
from app.utils.logging_config import get_logger


class TokenDetailService:
    """Service for token detail page APIs."""

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
    RANGE_TO_SECONDS: dict[str, int] = {
        "1d": 1 * 24 * 60 * 60,
        "7d": 7 * 24 * 60 * 60,
        "1m": 30 * 24 * 60 * 60,
        "3m": 90 * 24 * 60 * 60,
        "1y": 365 * 24 * 60 * 60,
    }
    INTERVAL_TO_SECONDS: dict[str, int] = {
        "15m": 15 * 60,
        "1h": 60 * 60,
        "4h": 4 * 60 * 60,
        "1d": 24 * 60 * 60,
        "1w": 7 * 24 * 60 * 60,
    }

    def __init__(self) -> None:
        self.logger = get_logger("app.services.token_detail_service")
        self.binance_client = BinanceClient()
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
        return "--" if price is None else f"{price:.2f} USDT"

    def _calc_limit_by_range_interval(self, normalized_range: str, use_interval: str) -> int:
        range_seconds = self.RANGE_TO_SECONDS.get(normalized_range)
        interval_seconds = self.INTERVAL_TO_SECONDS.get(use_interval)
        if not range_seconds or not interval_seconds:
            return self.RANGE_TO_LIMIT.get(normalized_range, 168)

        # Include the right boundary point; clamp to Binance max limit.
        points = (range_seconds + interval_seconds - 1) // interval_seconds
        return max(1, min(points + 1, 1000))

    @staticmethod
    def _klines_summary(points: list[TokenChartKlinePoint]) -> TokenChartSummary | None:
        if not points:
            return None

        start_price = points[0].open
        end_price = points[-1].close
        high_candidates = [p.high for p in points if p.high is not None]
        low_candidates = [p.low for p in points if p.low is not None]
        quote_volume_total = sum((p.quote_asset_volume or 0.0) for p in points)
        trades_total = sum((p.number_of_trades or 0) for p in points)

        change = None
        change_percent = None
        if start_price is not None and end_price is not None:
            change = end_price - start_price
            if start_price != 0:
                change_percent = change / start_price * 100

        return TokenChartSummary(
            start_price=start_price,
            end_price=end_price,
            change=change,
            change_percent=change_percent,
            high=max(high_candidates) if high_candidates else None,
            low=min(low_candidates) if low_candidates else None,
            total_quote_volume=quote_volume_total,
            total_trades=trades_total,
        )

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
            if str(token.get("symbol", "")).upper() != symbol:
                continue
            if not token.get("enabled", True):
                return None
            return token
        return None

    def _build_token_info(self, token_cfg: dict[str, Any], include_chart: bool, chart_range: str, chart_interval: str | None) -> TokenInfoBlock:
        symbol = str(token_cfg.get("symbol", "")).upper()
        pair = str(token_cfg.get("price_symbol", "") or f"{symbol}USDT").upper()

        price = None
        updated_at = None
        price_change_24h = None
        high_24h = None
        low_24h = None
        volume_24h = None
        status = "unavailable"

        try:
            cached = self.price_service.find_token_price(symbol)
            price = self.as_float(cached.get("price"))
            updated_at = self.to_iso_utc(cached.get("updated_at"))
            if price is not None:
                status = "partial"
        except Exception:
            self.logger.warning("Mongo price lookup failed symbol=%s", symbol)

        try:
            ticker = self.binance_client.get_24hr_ticker(pair)
            if price is None:
                price = self.as_float(ticker.get("lastPrice"))
            price_change_24h = self.as_float(ticker.get("priceChangePercent"))
            high_24h = self.as_float(ticker.get("highPrice"))
            low_24h = self.as_float(ticker.get("lowPrice"))
            volume_24h = self.as_float(ticker.get("quoteVolume"))
            updated_at = self.utc_now_iso()
            status = "online"
        except Exception:
            self.logger.warning("24hr ticker lookup failed pair=%s", pair)

        _ = include_chart
        _ = chart_range
        _ = chart_interval

        return TokenInfoBlock(
            symbol=symbol,
            name=str(token_cfg.get("name", "")),
            display_name=str(token_cfg.get("display_name", "")),
            logo=str(token_cfg.get("logo", "")),
            primary_chain=str(token_cfg.get("primary_chain", "")).lower(),
            category=str(token_cfg.get("category", "")),
            tags=token_cfg.get("tags") or [],
            price_display=self.format_price_display(price),
            price_change_24h=price_change_24h,
            high_24h=high_24h,
            low_24h=low_24h,
            volume_24h=volume_24h,
            updated_at=updated_at,
            status=status,
        )

    def build_chart(self, symbol: str, chart_range: str, interval: str | None = None) -> TokenChartResponse:
        token_cfg = self.get_token_config(symbol)
        if token_cfg is None:
            raise LookupError("TOKEN_NOT_FOUND")

        token_symbol = str(token_cfg.get("symbol", "")).upper()
        pair = str(token_cfg.get("price_symbol", "") or f"{token_symbol}USDT").upper()

        normalized_range = (chart_range or "7d").lower()
        if normalized_range not in self.RANGE_TO_INTERVAL:
            normalized_range = "7d"

        explicit_interval = interval is not None
        use_interval = (interval or self.RANGE_TO_INTERVAL[normalized_range]).lower()
        if use_interval not in self.SUPPORTED_INTERVALS:
            use_interval = self.RANGE_TO_INTERVAL[normalized_range]
            explicit_interval = False

        if explicit_interval:
            limit = self._calc_limit_by_range_interval(normalized_range, use_interval)
        else:
            limit = self.RANGE_TO_LIMIT.get(normalized_range, 168)

        try:
            klines = self.binance_client.get_klines(pair, use_interval, limit)
            points: list[TokenChartKlinePoint] = []
            for item in klines:
                if not isinstance(item, list) or len(item) < 11:
                    continue

                open_time = int(item[0])
                close_time = int(item[6]) if item[6] is not None else None
                open_time_iso = datetime.fromtimestamp(open_time / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
                close_time_iso = (
                    datetime.fromtimestamp(close_time / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
                    if close_time is not None
                    else None
                )

                trades = None
                try:
                    trades = int(item[8])
                except Exception:
                    trades = None

                points.append(
                    TokenChartKlinePoint(
                        open_time=open_time_iso,
                        close_time=close_time_iso,
                        open=self.as_float(item[1]),
                        high=self.as_float(item[2]),
                        low=self.as_float(item[3]),
                        close=self.as_float(item[4]),
                        volume=self.as_float(item[5]),
                        quote_asset_volume=self.as_float(item[7]),
                        number_of_trades=trades,
                    )
                )

            return TokenChartResponse(
                symbol=token_symbol,
                price_symbol=pair,
                range=normalized_range,
                interval=use_interval,
                source="binance",
                klines=points,
                summary=self._klines_summary(points),
            )
        except Exception:
            self.logger.warning("Chart lookup failed symbol=%s pair=%s", token_symbol, pair)
            return TokenChartResponse(
                symbol=token_symbol,
                price_symbol=pair,
                range=normalized_range,
                interval=use_interval,
                source="none",
                klines=[],
                summary=None,
            )

    def build_detail(
        self,
        symbol: str,
        include_chart: bool = True,
        chart_range: str = "7d",
        chart_interval: str | None = None,
    ) -> TokenDetailResponse:
        token_cfg = self.get_token_config(symbol)
        if token_cfg is None:
            raise LookupError("TOKEN_NOT_FOUND")

        info = self._build_token_info(
            token_cfg=token_cfg,
            include_chart=include_chart,
            chart_range=chart_range,
            chart_interval=chart_interval,
        )

        chart = None
        if include_chart:
            chart = self.build_chart(
                symbol=str(token_cfg.get("symbol", "")).upper(),
                chart_range=chart_range,
                interval=chart_interval,
            )

        return TokenDetailResponse(info=info, chart=chart)
