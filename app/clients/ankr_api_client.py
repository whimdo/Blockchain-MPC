from __future__ import annotations

from typing import Any
import requests
from configs.provider_config import load_provider_config


class AnkrAPIClient:
    """
    Ankr Advanced API ¿Í»§¶Ë
    """

    def __init__(self) -> None:
        config = load_provider_config()
        self.base_url = config.ankr_api_url

    def _post(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }

        response = requests.post(self.base_url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(f"Ankr API error: {data['error']}")

        return data.get("result", {})

    def get_account_balance(
        self,
        wallet_address: str,
        blockchain_names: list[str],
        page_size: int = 50,
    ) -> dict[str, Any]:
        return self._post(
            "ankr_getAccountBalance",
            {
                "walletAddress": wallet_address,
                "blockchain": blockchain_names,
                "pageSize": page_size,
            },
        )