from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


UserStatus = Literal["active", "disabled", "deleted"]


class ErrorResponse(BaseModel):
    code: str
    message: str


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=128)
    email: str | None = Field(default=None, max_length=128)
    display_name: str | None = Field(default=None, max_length=64)


class UserLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=128)


class UserPublic(BaseModel):
    user_id: str
    username: str
    email: str | None = None
    display_name: str | None = None
    status: UserStatus = "active"
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


class UserDocument(UserPublic):
    password_hash: str
    password_salt: str
    password_algorithm: str = "pbkdf2_sha256"


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class CurrentUserResponse(BaseModel):
    user: UserPublic
