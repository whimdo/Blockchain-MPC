import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class AuthConfig:
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    password_iterations: int


def load_auth_config() -> AuthConfig:
    """Load authentication config from environment variables."""
    return AuthConfig(
        jwt_secret_key=os.getenv("AUTH_JWT_SECRET_KEY", "dev-only-change-me"),
        jwt_algorithm=os.getenv("AUTH_JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")),
        password_iterations=int(os.getenv("AUTH_PASSWORD_ITERATIONS", "200000")),
    )
