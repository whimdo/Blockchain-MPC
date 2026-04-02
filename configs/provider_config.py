import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()

@dataclass
class ProviderConfig:
    ankr_rpc: dict[str, str]
    ankr_api_url: str
    binance_api_url: str


def load_provider_config() -> ProviderConfig:
    """从环境变量加载链服务与交易所提供方配置。"""
    return ProviderConfig(
        ankr_rpc={
            "ethereum": os.getenv("ANKR_RPC_ETH", ""),
            "bsc": os.getenv("ANKR_RPC_BSC", ""),
            "polygon": os.getenv("ANKR_RPC_POLYGON", ""),
        },
        ankr_api_url=os.getenv("ANKR_API_URL", "").rstrip("/"),
        binance_api_url=os.getenv("BINANCE_API_URL", "https://data-api.binance.vision").rstrip("/"),
    )
