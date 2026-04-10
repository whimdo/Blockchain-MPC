from __future__ import annotations

from typing import Any

import requests

from app.utils.logging_config import get_logger
from configs.ai_config import load_ai_config


class AIClient:
    """Simple OpenAI-compatible chat client."""

    def __init__(self) -> None:
        """Initialize AI client and load provider configuration."""
        self.logger = get_logger("app.clients.ai_client")
        config = load_ai_config()
        self.base_url = config.base_url
        self.api_key = config.api_key
        self.model = config.model
        self.timeout = config.timeout_seconds

    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 256,
    ) -> str:
        """Call chat completion API and return assistant content."""
        if not self.api_key:
            raise RuntimeError("Missing AI_API_KEY")

        url = f"{self.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            self.logger.info("AI chat request start model=%s", self.model)
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            if not content:
                raise RuntimeError(f"Empty completion response: {data}")

            self.logger.info("AI chat request success model=%s", self.model)
            return str(content).strip()
        except Exception:
            self.logger.exception("AI chat request failed model=%s", self.model)
            raise
