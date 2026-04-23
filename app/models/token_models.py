from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class Token:
    symbol: str
    name: str
    chain: str
    price: float | None = None
    currency: str = "USDT"
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class DashboardTokenOverview:
    """
    Single token row model for the Dashboard overview table.
    Field names follow the product/API spec.
    """

    symbol: str
    name: str
    chain: str
    price: float | None = None
    currency: str = "USDT"
    updated_at: datetime | None = None

    # Optional display fields for future UI enhancements.
    logo: str | None = None
    category: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DashboardOverviewResponse:
    """
    API response model for Dashboard overview.
    """

    items: list[DashboardTokenOverview] = field(default_factory=list)
    total: int = 0
    last_updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
