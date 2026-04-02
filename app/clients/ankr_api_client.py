from __future__ import annotations

from typing import Any

import requests

from app.utils.logging_config import get_logger
from configs.provider_config import load_provider_config


class AnkrAPIClient:
    """Client for Ankr Advanced API."""

    def __init__(self) -> None:
        """Initialize Ankr client and load base configuration."""
        self.logger = get_logger("app.clients.ankr_api_client")
        config = load_provider_config()
        self.base_url = config.ankr_api_url

    def _post(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Send a JSON-RPC POST request and return the result field."""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }

        try:
            self.logger.info("Calling Ankr API method=%s", method)
            response = requests.post(self.base_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise RuntimeError(f"Ankr API error: {data['error']}")

            return data.get("result", {})
        except Exception:
            self.logger.exception("Ankr API call failed for method=%s", method)
            raise

    def get_account_balance(
        self,
        wallet_address: str,
        blockchain_names: list[str],
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Query account balances across multiple chains."""
        try:
            return self._post(
                "ankr_getAccountBalance",
                {
                    "walletAddress": wallet_address,
                    "blockchain": blockchain_names,
                    "pageSize": page_size,
                },
            )
        except Exception:
            self.logger.exception(
                "Balance query failed for wallet=%s chains=%s",
                wallet_address,
                blockchain_names,
            )
            raise
