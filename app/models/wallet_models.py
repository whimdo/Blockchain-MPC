from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str


class WalletChainOption(BaseModel):
    key: str
    label: str
    enabled: bool = True


class WalletChainOptionsResponse(BaseModel):
    chains: list[WalletChainOption] = Field(default_factory=list)


class WalletAnalyzeRequest(BaseModel):
    address: str = Field(..., description="Wallet address to analyze")
    chains: list[str] = Field(default_factory=list, description="Ankr blockchain names, e.g. eth/bsc/polygon")


class WalletAssetItem(BaseModel):
    symbol: str
    name: str | None = None
    blockchain: str | None = None
    token_type: str | None = None
    contract_address: str | None = None
    balance: float | None = None
    display_balance: str | None = None
    price_usdt: float | None = None
    value_usdt: float = 0
    ratio: float = 0
    category: str = "other"
    logo: str | None = None
    tags: list[str] = Field(default_factory=list)


class WalletCategoryBreakdown(BaseModel):
    category: str
    label: str
    value_usdt: float
    ratio: float


class WalletGovernanceHint(BaseModel):
    symbol: str
    dao_name: str
    space_id: str
    value_usdt: float
    ratio: float


class WalletInsightResponse(BaseModel):
    address: str
    chains: list[str]
    chain_options: list[WalletChainOption] = Field(default_factory=list)
    asset_count: int
    priced_count: int
    total_value_usdt: float
    stablecoin_ratio: float
    mainstream_ratio: float
    defi_ratio: float
    meme_ratio: float
    governance_ratio: float
    concentration_ratio: float
    risk_level: str
    risk_label: str
    page_updated_at: str
    assets: list[WalletAssetItem] = Field(default_factory=list)
    category_breakdown: list[WalletCategoryBreakdown] = Field(default_factory=list)
    governance_hints: list[WalletGovernanceHint] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
