from app.clients.multichain_client import MultiChainClient
from app.utils.logging_config import get_logger


class ChainRPCService:
    """Service for chain RPC operations."""

    def __init__(self) -> None:
        """Initialize chain RPC service."""
        self.logger = get_logger("app.services.chain_rpc_service")
        self.client = MultiChainClient()

    def get_chain_health(self, chain: str) -> dict:
        """Get chain connectivity and latest block."""
        try:
            result = {
                "chain": chain,
                "connected": self.client.is_connected(chain),
                "latest_block": self.client.get_latest_block_number(chain),
            }
            self.logger.info("Chain health check succeeded chain=%s", chain)
            return result
        except Exception:
            self.logger.exception("Chain health check failed chain=%s", chain)
            raise

    def get_block_summary(self, chain: str, block_identifier: int | str = "latest") -> dict:
        """Get block summary for given block identifier."""
        try:
            result = self.client.get_block(chain, block_identifier)
            self.logger.info("Block summary fetched chain=%s identifier=%s", chain, block_identifier)
            return result
        except Exception:
            self.logger.exception("Block summary fetch failed chain=%s identifier=%s", chain, block_identifier)
            raise

    def get_transaction_detail(self, chain: str, tx_hash: str) -> dict:
        """Get transaction detail by hash."""
        try:
            result = self.client.get_transaction(chain, tx_hash)
            self.logger.info("Transaction detail fetched chain=%s tx_hash=%s", chain, tx_hash)
            return result
        except Exception:
            self.logger.exception("Transaction detail fetch failed chain=%s tx_hash=%s", chain, tx_hash)
            raise

    def get_address_native_balance(self, chain: str, address: str) -> dict:
        """Get native token balance for an address."""
        try:
            result = self.client.get_balance(chain, address)
            self.logger.info("Native balance fetched chain=%s address=%s", chain, address)
            return result
        except Exception:
            self.logger.exception("Native balance fetch failed chain=%s address=%s", chain, address)
            raise
