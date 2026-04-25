from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pymongo import ASCENDING, DESCENDING, ReturnDocument

from app.clients.mongo_client import MongoDBClient
from app.models.ai_assistant_models import (
    AIChatContext,
    AIChatMessage,
    AIChatMode,
    AIChatSessionDocument,
    AIChatSessionListResponse,
    AIChatSessionMetadata,
    AIChatSessionStatus,
    AIChatSessionSummary,
    AISuggestedQuestion,
    AIToolCallRecord,
)
from app.utils.logging_config import get_logger
from configs.mongo_config import load_mongo_config


class AIChatSessionServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class AIChatSessionService:
    """MongoDB persistence for one AI chat window per session document."""

    def __init__(self) -> None:
        self.logger = get_logger("app.services.ai_chat_session_service")
        self._mongo = MongoDBClient()
        self._mongo_cfg = load_mongo_config()
        self._ensure_indexes()

    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def new_id(prefix: str) -> str:
        return f"{prefix}-{uuid4().hex}"

    @property
    def collection_name(self) -> str:
        return self._mongo_cfg.ai_chat_sessions_collection

    @property
    def collection(self):
        return self._mongo.collection(self.collection_name)

    def _ensure_indexes(self) -> None:
        collection = self._mongo.collection(self._mongo_cfg.ai_chat_sessions_collection)
        collection.create_index([("updated_at", DESCENDING)])
        collection.create_index([("status", ASCENDING), ("updated_at", DESCENDING)])
        collection.create_index([("metadata.user_id", ASCENDING), ("updated_at", DESCENDING)])

    @staticmethod
    def _drop_mongo_id(doc: dict[str, Any] | None) -> dict[str, Any] | None:
        if doc is None:
            return None
        payload = dict(doc)
        mongo_id = payload.pop("_id", None)
        payload["session_id"] = str(payload.get("session_id") or mongo_id or "")
        return payload

    @classmethod
    def _doc_to_session(cls, doc: dict[str, Any] | None) -> AIChatSessionDocument | None:
        payload = cls._drop_mongo_id(doc)
        if payload is None:
            return None
        return AIChatSessionDocument(**payload)

    @staticmethod
    def _model_to_doc(model: Any) -> dict[str, Any]:
        payload = model.model_dump(mode="python")
        payload["_id"] = payload.pop("session_id")
        return payload

    @staticmethod
    def _session_filter(session_id: str, *, include_deleted: bool = False) -> dict[str, Any]:
        query: dict[str, Any] = {"_id": session_id}
        if not include_deleted:
            query["status"] = {"$ne": "deleted"}
        return query

    @staticmethod
    def _message_to_doc(message: AIChatMessage) -> dict[str, Any]:
        if message.message_id is None:
            message.message_id = AIChatSessionService.new_id("msg")
        if message.created_at is None:
            message.created_at = AIChatSessionService.utc_now()
        return message.model_dump(mode="python")

    @staticmethod
    def _tool_call_to_doc(tool_call: AIToolCallRecord) -> dict[str, Any]:
        if tool_call.tool_call_id is None:
            tool_call.tool_call_id = AIChatSessionService.new_id("tool")
        if tool_call.created_at is None:
            tool_call.created_at = AIChatSessionService.utc_now()
        return tool_call.model_dump(mode="python")

    @staticmethod
    def _summary_from_doc(doc: dict[str, Any]) -> AIChatSessionSummary:
        messages = list(doc.get("messages", []) or [])
        last_message = None
        if messages:
            last_message = str(messages[-1].get("content") or "")
        metadata = dict(doc.get("metadata") or {})
        return AIChatSessionSummary(
            session_id=str(doc.get("session_id") or doc.get("_id") or ""),
            title=doc.get("title"),
            mode=doc.get("mode", "auto"),
            status=doc.get("status", "active"),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
            message_count=int(metadata.get("message_count") or len(messages)),
            last_message=last_message,
        )

    def create_session(
        self,
        *,
        title: str | None = None,
        mode: AIChatMode = "auto",
        user_id: str | None = None,
        client: str | None = "web",
        session_id: str | None = None,
    ) -> AIChatSessionDocument:
        now = self.utc_now()
        session = AIChatSessionDocument(
            session_id=session_id or self.new_id("session"),
            title=title,
            mode=mode,
            status="active",
            created_at=now,
            updated_at=now,
            metadata=AIChatSessionMetadata(user_id=user_id, client=client),
        )
        self.collection.insert_one(self._model_to_doc(session))
        return session

    def get_session(self, session_id: str) -> AIChatSessionDocument | None:
        sid = (session_id or "").strip()
        if not sid:
            raise AIChatSessionServiceError(400, "SESSION_ID_REQUIRED", "Field 'session_id' is required.")
        doc = self.collection.find_one(self._session_filter(sid))
        return self._doc_to_session(doc)

    def require_session(self, session_id: str) -> AIChatSessionDocument:
        session = self.get_session(session_id)
        if session is None:
            raise AIChatSessionServiceError(404, "SESSION_NOT_FOUND", "AI chat session not found.")
        return session

    def append_message(self, session_id: str, message: AIChatMessage) -> AIChatMessage:
        sid = (session_id or "").strip()
        if not sid:
            raise AIChatSessionServiceError(400, "SESSION_ID_REQUIRED", "Field 'session_id' is required.")

        message_doc = self._message_to_doc(message)
        result = self.collection.update_one(
            self._session_filter(sid),
            {
                "$push": {"messages": message_doc},
                "$inc": {"metadata.message_count": 1},
                "$set": {"updated_at": self.utc_now()},
            },
        )
        if result.matched_count == 0:
            raise AIChatSessionServiceError(404, "SESSION_NOT_FOUND", "AI chat session not found.")
        return AIChatMessage(**message_doc)

    def append_tool_calls(self, session_id: str, tool_calls: list[AIToolCallRecord]) -> list[AIToolCallRecord]:
        sid = (session_id or "").strip()
        if not sid:
            raise AIChatSessionServiceError(400, "SESSION_ID_REQUIRED", "Field 'session_id' is required.")
        if not tool_calls:
            return []

        tool_docs = [self._tool_call_to_doc(tool_call) for tool_call in tool_calls]
        result = self.collection.update_one(
            self._session_filter(sid),
            {
                "$push": {"tool_calls": {"$each": tool_docs}},
                "$inc": {"metadata.tool_call_count": len(tool_docs)},
                "$set": {"updated_at": self.utc_now()},
            },
        )
        if result.matched_count == 0:
            raise AIChatSessionServiceError(404, "SESSION_NOT_FOUND", "AI chat session not found.")
        return [AIToolCallRecord(**item) for item in tool_docs]

    def update_context(self, session_id: str, context: AIChatContext) -> AIChatContext:
        sid = (session_id or "").strip()
        if not sid:
            raise AIChatSessionServiceError(400, "SESSION_ID_REQUIRED", "Field 'session_id' is required.")

        result = self.collection.update_one(
            self._session_filter(sid),
            {"$set": {"context": context.model_dump(mode="python"), "updated_at": self.utc_now()}},
        )
        if result.matched_count == 0:
            raise AIChatSessionServiceError(404, "SESSION_NOT_FOUND", "AI chat session not found.")
        return context

    def update_suggested_questions(
        self,
        session_id: str,
        suggested_questions: list[AISuggestedQuestion],
    ) -> list[AISuggestedQuestion]:
        sid = (session_id or "").strip()
        if not sid:
            raise AIChatSessionServiceError(400, "SESSION_ID_REQUIRED", "Field 'session_id' is required.")

        result = self.collection.update_one(
            self._session_filter(sid),
            {
                "$set": {
                    "suggested_questions": [item.model_dump(mode="python") for item in suggested_questions],
                    "updated_at": self.utc_now(),
                }
            },
        )
        if result.matched_count == 0:
            raise AIChatSessionServiceError(404, "SESSION_NOT_FOUND", "AI chat session not found.")
        return suggested_questions

    def update_status(self, session_id: str, status: AIChatSessionStatus) -> AIChatSessionDocument:
        sid = (session_id or "").strip()
        if not sid:
            raise AIChatSessionServiceError(400, "SESSION_ID_REQUIRED", "Field 'session_id' is required.")

        doc = self.collection.find_one_and_update(
            self._session_filter(sid, include_deleted=True),
            {"$set": {"status": status, "updated_at": self.utc_now()}},
            return_document=ReturnDocument.AFTER,
        )
        session = self._doc_to_session(doc)
        if session is None:
            raise AIChatSessionServiceError(404, "SESSION_NOT_FOUND", "AI chat session not found.")
        return session

    def update_session(
        self,
        session_id: str,
        *,
        title: str | None = None,
        status: AIChatSessionStatus | None = None,
    ) -> AIChatSessionDocument:
        sid = (session_id or "").strip()
        if not sid:
            raise AIChatSessionServiceError(400, "SESSION_ID_REQUIRED", "Field 'session_id' is required.")

        update_fields: dict[str, Any] = {"updated_at": self.utc_now()}
        if title is not None:
            update_fields["title"] = title
        if status is not None:
            update_fields["status"] = status

        doc = self.collection.find_one_and_update(
            self._session_filter(sid, include_deleted=True),
            {"$set": update_fields},
            return_document=ReturnDocument.AFTER,
        )
        session = self._doc_to_session(doc)
        if session is None:
            raise AIChatSessionServiceError(404, "SESSION_NOT_FOUND", "AI chat session not found.")
        return session

    def list_sessions(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: AIChatSessionStatus | None = None,
        user_id: str | None = None,
    ) -> AIChatSessionListResponse:
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 20)))
        query: dict[str, Any] = {"status": {"$ne": "deleted"}}
        if status is not None:
            query["status"] = status
        if user_id:
            query["metadata.user_id"] = user_id

        total = self.collection.count_documents(query)
        cursor = self.collection.find(
            query,
            sort=[("updated_at", DESCENDING)],
            skip=(page - 1) * page_size,
            limit=page_size,
            projection={
                "title": 1,
                "mode": 1,
                "status": 1,
                "created_at": 1,
                "updated_at": 1,
                "metadata.message_count": 1,
                "messages": {"$slice": -1},
            },
        )
        return AIChatSessionListResponse(
            page=page,
            page_size=page_size,
            total=total,
            sessions=[self._summary_from_doc(doc) for doc in cursor],
        )

    def soft_delete_session(self, session_id: str) -> AIChatSessionDocument:
        return self.update_status(session_id=session_id, status="deleted")
