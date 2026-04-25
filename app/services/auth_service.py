from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from jwt import ExpiredSignatureError, InvalidTokenError
from pymongo import ASCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.clients.auth_client import JWTClient, PasswordHashClient
from app.clients.mongo_client import MongoDBClient
from app.models.auth_models import (
    AuthTokenResponse,
    UserDocument,
    UserLoginRequest,
    UserPublic,
    UserRegisterRequest,
)
from app.utils.logging_config import get_logger
from configs.mongo_config import load_mongo_config


class AuthServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class AuthService:
    """User registration, login, password storage, and token verification."""

    def __init__(self) -> None:
        self.logger = get_logger("app.services.auth_service")
        self._mongo = MongoDBClient()
        self._mongo_cfg = load_mongo_config()
        self.password_client = PasswordHashClient()
        self.jwt_client = JWTClient()
        self._ensure_indexes()

    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def normalize_username(username: str) -> str:
        return (username or "").strip().lower()

    @staticmethod
    def normalize_email(email: str | None) -> str | None:
        value = (email or "").strip().lower()
        return value or None

    @property
    def collection(self):
        return self._mongo.collection(self._mongo_cfg.users_collection)

    def _ensure_indexes(self) -> None:
        collection = self._mongo.collection(self._mongo_cfg.users_collection)
        collection.create_index([("username", ASCENDING)], unique=True)
        collection.create_index([("email", ASCENDING)], unique=True, sparse=True)
        collection.create_index([("status", ASCENDING)])

    @staticmethod
    def _doc_to_user(doc: dict[str, Any] | None) -> UserDocument | None:
        if doc is None:
            return None
        payload = dict(doc)
        mongo_id = payload.pop("_id", None)
        payload["user_id"] = str(payload.get("user_id") or mongo_id or "")
        return UserDocument(**payload)

    @staticmethod
    def to_public(user: UserDocument) -> UserPublic:
        return UserPublic(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )

    def register(self, req: UserRegisterRequest) -> AuthTokenResponse:
        username = self.normalize_username(req.username)
        email = self.normalize_email(req.email)
        now = self.utc_now()
        user_id = f"user-{uuid4().hex}"
        password_hash, password_salt = self.password_client.hash_password(req.password)

        user = UserDocument(
            user_id=user_id,
            username=username,
            email=email,
            display_name=req.display_name or username,
            status="active",
            created_at=now,
            updated_at=now,
            last_login_at=now,
            password_hash=password_hash,
            password_salt=password_salt,
            password_algorithm=self.password_client.algorithm,
        )
        doc = user.model_dump(mode="python")
        doc["_id"] = doc.pop("user_id")

        try:
            self.collection.insert_one(doc)
        except DuplicateKeyError as exc:
            raise AuthServiceError(409, "USER_ALREADY_EXISTS", "Username or email already exists.") from exc

        return self._token_response(user)

    def login(self, req: UserLoginRequest) -> AuthTokenResponse:
        identity = self.normalize_username(req.username)
        user = self._doc_to_user(
            self.collection.find_one(
                {
                    "$or": [
                        {"username": identity},
                        {"email": identity},
                    ],
                    "status": "active",
                }
            )
        )
        if user is None:
            raise AuthServiceError(401, "INVALID_CREDENTIALS", "Invalid username or password.")

        if not self.password_client.verify_password(req.password, user.password_hash, user.password_salt):
            raise AuthServiceError(401, "INVALID_CREDENTIALS", "Invalid username or password.")

        doc = self.collection.find_one_and_update(
            {"_id": user.user_id},
            {"$set": {"last_login_at": self.utc_now(), "updated_at": self.utc_now()}},
            return_document=ReturnDocument.AFTER,
        )
        updated_user = self._doc_to_user(doc) or user
        return self._token_response(updated_user)

    def get_user_by_id(self, user_id: str) -> UserDocument | None:
        uid = (user_id or "").strip()
        if not uid:
            return None
        return self._doc_to_user(self.collection.find_one({"_id": uid, "status": "active"}))

    def current_user_from_token(self, token: str) -> UserPublic:
        try:
            payload = self.jwt_client.decode_access_token(token)
        except ExpiredSignatureError as exc:
            raise AuthServiceError(401, "TOKEN_EXPIRED", "Access token has expired.") from exc
        except (InvalidTokenError, ValueError) as exc:
            raise AuthServiceError(401, "INVALID_TOKEN", "Invalid access token.") from exc

        user = self.get_user_by_id(str(payload.get("sub") or ""))
        if user is None:
            raise AuthServiceError(401, "USER_NOT_FOUND", "User not found or disabled.")
        return self.to_public(user)

    def _token_response(self, user: UserDocument) -> AuthTokenResponse:
        return AuthTokenResponse(
            access_token=self.jwt_client.create_access_token(user_id=user.user_id, username=user.username),
            expires_in=self.jwt_client.expires_in_seconds,
            user=self.to_public(user),
        )
