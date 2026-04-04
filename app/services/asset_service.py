from app.clients.ankr_api_client import AnkrAPIClient
from app.storage.market_storage import MarketStorage
from app.utils.logging_config import get_logger


class AssetService:
    """Service for chain asset queries."""
    def __init__(self) -> None:
        """Initialize asset service."""
        self.logger = get_logger("app.services.asset_service")
        self.client = AnkrAPIClient()
        self.storage = MarketStorage()

    def get_multichain_assets(self, address: str, chains: list[str]) -> dict:
        """Query wallet assets across multiple chains."""
        try:
            self.logger.info("Querying multi-chain assets address=%s chains=%s", address, chains)
            result = self.client.get_account_balance(
                wallet_address=address,
                blockchain_names=chains,
            )
            try:
                inserted_id = self.storage.save_ankr_raw_assets(address, chains, result)
                self.logger.info("Stored raw Ankr assets inserted_id=%s", inserted_id)
            except Exception:
                self.logger.exception(
                    "Failed to store raw Ankr assets address=%s chains=%s",
                    address,
                    chains,
                )
            return result
        except Exception:
            self.logger.exception("Multi-chain asset query failed address=%s chains=%s", address, chains)
            raise
