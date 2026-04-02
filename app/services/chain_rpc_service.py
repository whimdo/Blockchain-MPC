from app.clients.multichain_client import MultiChainClient


class ChainRPCService:
    def __init__(self) -> None:
        self.client = MultiChainClient()

    def get_chain_health(self, chain: str) -> dict:
        return {
            "chain": chain,
            "connected": self.client.is_connected(chain),
            "latest_block": self.client.get_latest_block_number(chain),
        }

    def get_block_summary(self, chain: str, block_identifier: int | str = "latest") -> dict:
        return self.client.get_block(chain, block_identifier)

    def get_transaction_detail(self, chain: str, tx_hash: str) -> dict:
        return self.client.get_transaction(chain, tx_hash)

    def get_address_native_balance(self, chain: str, address: str) -> dict:
        return self.client.get_balance(chain, address)