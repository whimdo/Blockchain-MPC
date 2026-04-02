from __future__ import annotations

from typing import Any
from web3 import Web3
from configs.provider_config import load_provider_config


class MultiChainClient:
    """
    统一多链客户端（基于 Ankr RPC）
    """

    def __init__(self) -> None:
        config = load_provider_config()
        self.providers: dict[str, Web3] = {}

        for chain, rpc_url in config.ankr_rpc.items():
            if rpc_url:
                self.providers[chain] = Web3(Web3.HTTPProvider(rpc_url))

    def get_client(self, chain: str) -> Web3:
        if chain not in self.providers:
            raise ValueError(f"Unsupported chain: {chain}")
        return self.providers[chain]

    def is_connected(self, chain: str) -> bool:
        return self.get_client(chain).is_connected()

    def get_latest_block_number(self, chain: str) -> int:
        return self.get_client(chain).eth.block_number

    def get_block(self, chain: str, block_identifier: int | str = "latest") -> dict[str, Any]:
        w3 = self.get_client(chain)
        block = w3.eth.get_block(block_identifier)

        return {
            "chain": chain,
            "number": block["number"],
            "hash": block["hash"].hex(),
            "timestamp": block["timestamp"],
            "tx_count": len(block["transactions"]),
        }

    def get_transaction(self, chain: str, tx_hash: str) -> dict[str, Any]:
        w3 = self.get_client(chain)
        tx = w3.eth.get_transaction(tx_hash)

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

    def get_balance(self, chain: str, address: str) -> dict[str, Any]:
        w3 = self.get_client(chain)
        checksum = Web3.to_checksum_address(address)
        balance_wei = w3.eth.get_balance(checksum)

        return {
            "chain": chain,
            "address": checksum,
            "balance_wei": balance_wei,
            "balance_eth": str(w3.from_wei(balance_wei, "ether")),
        }

    def get_logs(
        self,
        chain: str,
        from_block: int,
        to_block: int | str,
        address: str | None = None,
        topics: list[str] | None = None,
    ) -> list[dict[str, Any]]:
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