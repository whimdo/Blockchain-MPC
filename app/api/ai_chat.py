from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.models.ai_assistant_models import (
    AIChatRequest,
    AIChatResponse,
    AIChatSessionCreateRequest,
    AIChatSessionDocument,
    AIChatSessionListResponse,
    AIChatSessionStatus,
    AIChatSessionUpdateRequest,
    ErrorResponse,
)
from app.services.ai_chat_service import AIChatService, AIChatServiceError
from app.services.ai_chat_session_service import AIChatSessionServiceError
from app.utils.logging_config import get_logger


logger = get_logger("app.api.ai_chat")
router = APIRouter(prefix="/api/ai", tags=["ai-chat"])
_service: AIChatService | None = None


def get_service() -> AIChatService:
    global _service
    if _service is None:
        _service = AIChatService()
    return _service


def _json_error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"code": code, "message": message})


@router.post(
    "/chat",
    response_model=AIChatResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="AI Chat",
)
async def chat(req: AIChatRequest) -> Any:
    try:
        return await get_service().chat(req)
    except AIChatSessionServiceError as exc:
        return _json_error(exc.status_code, exc.code, exc.message)
    except AIChatServiceError as exc:
        return _json_error(exc.status_code, exc.code, exc.message)
    except Exception:
        logger.exception("Unexpected error in AI chat endpoint")
        return _json_error(500, "AI_CHAT_ERROR", "Failed to process AI chat request.")


@router.post(
    "/sessions",
    response_model=AIChatSessionDocument,
    responses={500: {"model": ErrorResponse}},
    summary="Create AI Chat Session",
)
def create_session(req: AIChatSessionCreateRequest) -> Any:
    try:
        return get_service().session_service.create_session(
            title=req.title,
            mode=req.mode,
            user_id=req.user_id,
            client=req.client,
        )
    except Exception:
        logger.exception("Unexpected error in AI chat session create endpoint")
        return _json_error(500, "AI_SESSION_CREATE_ERROR", "Failed to create AI chat session.")


@router.get(
    "/sessions",
    response_model=AIChatSessionListResponse,
    responses={500: {"model": ErrorResponse}},
    summary="AI Chat Session List",
)
def list_sessions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: AIChatSessionStatus | None = Query(default=None),
    user_id: str | None = Query(default=None),
) -> Any:
    try:
        return get_service().session_service.list_sessions(
            page=page,
            page_size=page_size,
            status=status,
            user_id=user_id,
        )
    except AIChatSessionServiceError as exc:
        return _json_error(exc.status_code, exc.code, exc.message)
    except Exception:
        logger.exception("Unexpected error in AI chat session list endpoint")
        return _json_error(500, "AI_SESSION_LIST_ERROR", "Failed to load AI chat sessions.")


@router.get(
    "/sessions/{session_id}",
    response_model=AIChatSessionDocument,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="AI Chat Session Detail",
)
def get_session(session_id: str) -> Any:
    try:
        return get_service().session_service.require_session(session_id)
    except AIChatSessionServiceError as exc:
        return _json_error(exc.status_code, exc.code, exc.message)
    except Exception:
        logger.exception("Unexpected error in AI chat session detail endpoint session_id=%s", session_id)
        return _json_error(500, "AI_SESSION_DETAIL_ERROR", "Failed to load AI chat session.")


@router.patch(
    "/sessions/{session_id}",
    response_model=AIChatSessionDocument,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Update AI Chat Session",
)
def update_session(session_id: str, req: AIChatSessionUpdateRequest) -> Any:
    try:
        return get_service().session_service.update_session(
            session_id=session_id,
            title=req.title,
            status=req.status,
        )
    except AIChatSessionServiceError as exc:
        return _json_error(exc.status_code, exc.code, exc.message)
    except Exception:
        logger.exception("Unexpected error in AI chat session update endpoint session_id=%s", session_id)
        return _json_error(500, "AI_SESSION_UPDATE_ERROR", "Failed to update AI chat session.")


@router.delete(
    "/sessions/{session_id}",
    response_model=AIChatSessionDocument,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Delete AI Chat Session",
)
def delete_session(session_id: str) -> Any:
    try:
        return get_service().session_service.soft_delete_session(session_id)
    except AIChatSessionServiceError as exc:
        return _json_error(exc.status_code, exc.code, exc.message)
    except Exception:
        logger.exception("Unexpected error in AI chat session delete endpoint session_id=%s", session_id)
        return _json_error(500, "AI_SESSION_DELETE_ERROR", "Failed to delete AI chat session.")
