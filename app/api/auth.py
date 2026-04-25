from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from app.models.auth_models import (
    AuthTokenResponse,
    CurrentUserResponse,
    ErrorResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.services.auth_service import AuthService, AuthServiceError
from app.utils.logging_config import get_logger


logger = get_logger("app.api.auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])
_service: AuthService | None = None


def get_service() -> AuthService:
    global _service
    if _service is None:
        _service = AuthService()
    return _service


def _json_error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"code": code, "message": message})


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise AuthServiceError(401, "AUTHORIZATION_REQUIRED", "Authorization header is required.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthServiceError(401, "INVALID_AUTHORIZATION_HEADER", "Authorization header must be Bearer token.")
    return token.strip()


@router.post(
    "/register",
    response_model=AuthTokenResponse,
    responses={409: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Register User",
)
def register(req: UserRegisterRequest) -> Any:
    try:
        return get_service().register(req)
    except AuthServiceError as exc:
        return _json_error(exc.status_code, exc.code, exc.message)
    except Exception:
        logger.exception("Unexpected error in register endpoint")
        return _json_error(500, "REGISTER_ERROR", "Failed to register user.")


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Login User",
)
def login(req: UserLoginRequest) -> Any:
    try:
        return get_service().login(req)
    except AuthServiceError as exc:
        return _json_error(exc.status_code, exc.code, exc.message)
    except Exception:
        logger.exception("Unexpected error in login endpoint")
        return _json_error(500, "LOGIN_ERROR", "Failed to login.")


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Current User",
)
def me(authorization: str | None = Header(default=None)) -> Any:
    try:
        token = extract_bearer_token(authorization)
        return CurrentUserResponse(user=get_service().current_user_from_token(token))
    except AuthServiceError as exc:
        return _json_error(exc.status_code, exc.code, exc.message)
    except Exception:
        logger.exception("Unexpected error in me endpoint")
        return _json_error(500, "CURRENT_USER_ERROR", "Failed to load current user.")
