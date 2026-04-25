from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from configs.auth_config import AuthConfig, load_auth_config


class PasswordHashClient:
    """Password hashing helper based on PBKDF2-HMAC-SHA256."""

    algorithm = "pbkdf2_sha256"

    def __init__(self, config: AuthConfig | None = None) -> None:
        self.config = config or load_auth_config()

    def hash_password(self, password: str) -> tuple[str, str]:
        salt = secrets.token_hex(16)
        password_hash = self._pbkdf2(password=password, salt=salt)
        return password_hash, salt

    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        candidate = self._pbkdf2(password=password, salt=salt)
        return hmac.compare_digest(candidate, password_hash)

    def _pbkdf2(self, *, password: str, salt: str) -> str:
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            self.config.password_iterations,
        )
        return digest.hex()


class JWTClient:
    """JWT helper for access token generation and verification."""

    def __init__(self, config: AuthConfig | None = None) -> None:
        self.config = config or load_auth_config()

    @property
    def expires_in_seconds(self) -> int:
        return self.config.access_token_expire_minutes * 60

    def create_access_token(self, *, user_id: str, username: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "username": username,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self.config.access_token_expire_minutes)).timestamp()),
            "type": "access",
        }
        return jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        payload = jwt.decode(token, self.config.jwt_secret_key, algorithms=[self.config.jwt_algorithm])
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        return dict(payload)
