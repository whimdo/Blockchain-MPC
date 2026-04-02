from __future__ import annotations

from typing import Any

from web3 import Web3

from app.utils.logging_config import get_logger
from configs.provider_config import load_provider_config


class MultiChainClient:
    """Unified multi-chain client based on Ankr RPC."""

    def __init__(self) -> None:
        """Initialize Web3 providers for configured chains."""
        self.logger = get_logger("app.clients.multichain_client")
        config = load_provider_config()
        self.providers: dict[str, Web3] = {}

        for chain, rpc_url in config.ankr_rpc.items():
            if rpc_url:
                self.providers[chain] = Web3(Web3.HTTPProvider(rpc_url))

        self.logger.info("Initialized providers for chains=%s", list(self.providers.keys()))

    def get_client(self, chain: str) -> Web3:
        """Get Web3 client by chain name."""
        if chain not in self.providers:
            self.logger.error("Unsupported chain=%s", chain)
            raise ValueError(f"Unsupported chain: {chain}")
        return self.providers[chain]

    def is_connected(self, chain: str) -> bool:
        """Check RPC connectivity for a chain."""
        try:
            connected = self.get_client(chain).is_connected()
            self.logger.info("Connectivity check chain=%s connected=%s", chain, connected)
            return connected
        except Exception:
            self.logger.exception("Connectivity check failed chain=%s", chain)
            raise

    def get_latest_block_number(self, chain: str) -> int:
        """Get latest block number for a chain."""
        try:
            block_number = self.get_client(chain).eth.block_number
            self.logger.info("Latest block fetched chain=%s block=%s", chain, block_number)
            return block_number
        except Exception:
            self.logger.exception("Failed to fetch latest block chain=%s", chain)
            raise

    def get_block(self, chain: str, block_identifier: int | str = "latest") -> dict[str, Any]:
        """Get block summary by block identifier."""
        try:
            w3 = self.get_client(chain)
            block = w3.eth.get_block(block_identifier)
            self.logger.info("Block fetched chain=%s identifier=%s", chain, block_identifier)
            return {
                "chain": chain,
                "number": block["number"],
                "hash": block["hash"].hex(),
                "timestamp": block["timestamp"],
                "tx_count": len(block["transactions"]),
            }
        except Exception:
            self.logger.exception("Failed to fetch block chain=%s identifier=%s", chain, block_identifier)
            raise

    def get_transaction(self, chain: str, tx_hash: str) -> dict[str, Any]:
        """Get transaction detail by transaction hash."""
        try:
            w3 = self.get_client(chain)
            tx = w3.eth.get_transaction(tx_hash)
            self.logger.info("Transaction fetched chain=%s tx_hash=%s", chain, tx_hash)
            return {
                "chain": chain,
                "tx_hash": tx["hash"].hex(),
                "from": tx["from"],
                "to": tx["to"],
                "value_wei": tx["value"],
                "gas": tx["gas"],
                "block_number": tx["blockNumber"],
                "input": tx["input"].hex() if isinstance(tx["input"], bytes) else tx["input"],
            }
        except Exception:
            self.logger.exception("Failed to fetch transaction chain=%s tx_hash=%s", chain, tx_hash)
            raise

    def get_balance(self, chain: str, address: str) -> dict[str, Any]:
        """Get native token balance for an address."""
        try:
            w3 = self.get_client(chain)
            checksum = Web3.to_checksum_address(address)
            balance_wei = w3.eth.get_balance(checksum)
            self.logger.info("Balance fetched chain=%s address=%s", chain, checksum)
            return {
                "chain": chain,
                "address": checksum,
                "balance_wei": balance_wei,
                "balance_eth": str(w3.from_wei(balance_wei, "ether")),
            }
        except Exception:
            self.logger.exception("Failed to fetch balance chain=%s address=%s", chain, address)
            raise

    def get_logs(
        self,
        chain: str,
        from_block: int,
        to_block: int | str,
        address: str | None = None,
        topics: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query on-chain logs by range and optional filters."""
        try:
            w3 = self.get_client(chain)
            params: dict[str, Any] = {
                "fromBlock": from_block,
                "toBlock": to_block,
            }

            if address:
                params["address"] = Web3.to_checksum_address(address)

            if topics:
                params["topics"] = topics

            logs = w3.eth.get_logs(params)
            self.logger.info(
                "Logs fetched chain=%s from=%s to=%s count=%s",
                chain,
                from_block,
                to_block,
                len(logs),
            )

            return [
                {
                    "chain": chain,
                    "block_number": log["blockNumber"],
                    "tx_hash": log["transactionHash"].hex(),
                    "address": log["address"],
                    "topics": [t.hex() for t in log["topics"]],
                    "data": log["data"].hex() if isinstance(log["data"], bytes) else log["data"],
                    "log_index": log["logIndex"],
                }
                for log in logs
            ]
        except Exception:
            self.logger.exception(
                "Failed to fetch logs chain=%s from=%s to=%s address=%s",
                chain,
                from_block,
                to_block,
                address,
            )
            raise
