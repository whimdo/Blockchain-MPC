from dataclasses import dataclass, field
from typing import Any, Optional, List

@dataclass
class Asset:
    blockchain: str# 所属链，如 "eth"、"bsc"、"polygon"
    tokenName: str# 代币名称，如 "Ether"、"Binance Coin"
    tokenSymbol: str# 代币符号，如 "ETH"、"BNB"
    tokenDecimals: int# 代币小数位数，如 18
    tokenType: str# 代币类型，如 "ERC20"、"BEP20"，原生代币可标记为 "NATIVE"

    contractAddress: Optional[str] = None# 合约地址，对于原生代币通常为 None
    holderAddress: Optional[str] = None# 持有地址，通常与 holderAddress 相同，但对于某些链（如 Solana）可能不同
    balance: Optional[str] = None# 以字符串形式表示的余额，单位为最小单位（如 wei、satoshi）
    balanceRawInteger: Optional[int] = None# 以整数形式表示的余额，单位为最小单位（如 wei、satoshi），方便计算
    balanceUsd: Optional[float] = None# 以美元计价的余额估值，可能需要通过市场价格计算得出
    tokenPrice: Optional[float] = None# 以美元计价的单价，可能需要通过市场价格查询得出
    thumbnail: Optional[str] = None# 资产图标 URL，可能需要通过第三方服务查询得出

    is_native: bool = False# 是否为原生代币（如 ETH、BNB），如果是则 contractAddress 可选且通常为 None
    is_stablecoin: bool = False# 是否为稳定币，可以通过 tokenSymbol 或市场数据判断得出

@dataclass
class WalletAssetOverview:
    address: str
    chains: List[str]
    assets: List[Asset] = field(default_factory=list)
    asset_count: int = 0
    priced_count: int = 0
    total_value_usdt: float = 0.0

@dataclass
class MarketPrice:
    symbol: str
    price: float
    source: str = "binance"

@dataclass
class RawAssetData:
    address: str
    raw_result: Any
    source: str = "ankr_api"