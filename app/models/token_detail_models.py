from __future__ import annotations

from typing import Any

from typing import Literal
from pydantic import BaseModel, Field


class TokenInfoBlock(BaseModel):
    symbol: str
    name: str
    display_name: str
    logo: str | None = None
    primary_chain: str
    category: str
    tags: list[str] = Field(default_factory=list)
    price_display: str | None = None
    price_change_24h: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
    volume_24h: float | None = None
    updated_at: str | None = None
    status: str | None = None

class TokenChartKlinePoint(BaseModel):
    open_time: str
    close_time: str | None = None

    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None

    volume: float | None = None
    quote_asset_volume: float | None = None
    number_of_trades: int | None = None

class TokenChartSummary(BaseModel):
    start_price: float | None = None
    end_price: float | None = None
    change: float | None = None
    change_percent: float | None = None
    high: float | None = None
    low: float | None = None
    total_quote_volume: float | None = None
    total_trades: int | None = None

class TokenChartRequest(BaseModel):
    symbol: str = Field(..., description="代币符号，例如 BTC、ETH、DOGE")

    range: Literal["1d", "7d", "1m", "3m", "1y"] = Field(
        default="7d",
        description="图表时间范围",
    )

    interval: Literal["15m", "1h", "4h", "1d", "1w"] | None = Field(
        default=None,
        description="K线粒度；为空时后端按 range 自动推断",
    )

    source: Literal["binance", "coingecko", "mongo"] = Field(
        default="binance",
        description="行情数据来源",
    )

class TokenChartResponse(BaseModel):
    symbol: str
    price_symbol: str
    range: str
    interval: str
    source: str
    klines: list[TokenChartKlinePoint]
    summary: TokenChartSummary | None = None



class TokenDetailRequest(BaseModel):
    symbol: str = Field(..., description="代币符号，例如 BTC、ETH、DOGE")

    include_chart: bool = Field(
        default=True,
        description="是否在详情响应中附带图表数据",
    )

    chart_range: Literal["1d", "7d", "1m", "3m", "1y"] = Field(
        default="7d",
        description="图表时间范围",
    )

    chart_interval: Literal["15m", "1h", "4h", "1d", "1w"] | None = Field(
        default="1d",
        description="K线粒度；为空时后端自动推断",
    )

    chart_source: Literal["binance", "coingecko", "mongo"] = Field(
        default="binance",
        description="图表数据来源",
    )


class TokenDetailResponse(BaseModel):
    info: TokenInfoBlock
    chart: TokenChartResponse | None = None
    

# class TokenPrimaryChainInfo(BaseModel):#代币所在主链的情况

class TokenAISummary(BaseModel):
    symbol: str
    title: str
    summary: str
    key_points: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    generated_by: str = "template"
    generated_at: str

class TokenAISummaryRequest(BaseModel):
    symbol: str
    chart_summary: TokenChartSummary | None = None

class TokenAISummaryResponse(BaseModel):
    symbol: str
    summary: TokenAISummary | None = None
