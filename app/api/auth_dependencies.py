from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException

from app.models.auth_models import UserPublic
from app.services.auth_service import AuthService, AuthServiceError


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> UserPublic:
    if not authorization:
        raise HTTPException(status_code=401, detail={"code": "AUTHORIZATION_REQUIRED", "message": "Authorization header is required."})

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_AUTHORIZATION_HEADER", "message": "Authorization header must be Bearer token."},
        )

    try:
        return AuthService().current_user_from_token(token.strip())
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message}) from exc
