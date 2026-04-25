import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class AIConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int


def load_ai_config() -> AIConfig:
    """Load AI provider config from environment variables."""
    return AIConfig(
        base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        api_key=os.getenv("AI_API_KEY", ""),
        model=os.getenv("AI_MODEL", "gpt-4o-mini"),
        timeout_seconds=int(os.getenv("AI_TIMEOUT_SECONDS", "30")),
    )
