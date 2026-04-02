from app.clients.ankr_api_client import AnkrAPIClient


class AssetService:
    def __init__(self) -> None:
        self.client = AnkrAPIClient()

    def get_multichain_assets(self, address: str, chains: list[str]) -> dict:
        return self.client.get_account_balance(
            wallet_address=address,
            blockchain_names=chains,
        )