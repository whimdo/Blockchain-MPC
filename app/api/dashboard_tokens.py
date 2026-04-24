from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.dashboard_tokens_models import (
    ErrorResponse,
    TokenCard,
    TokenOverviewResponse,
    TokenRefreshAllResponse,
    TokenRefreshRequest,
)
from app.services.dashboard_tokens_service import DashboardTokensService
from app.utils.logging_config import get_logger


logger = get_logger("app.api.dashboard_tokens")
router = APIRouter(prefix="/api/dashboard/tokens", tags=["dashboard-tokens"])
service = DashboardTokensService()


@router.get(
    "/overview",
    response_model=TokenOverviewResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_dashboard_tokens_overview() -> TokenOverviewResponse:
    try:
        return service.get_overview()
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": "DASHBOARD_OVERVIEW_ERROR", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=detail)
    except Exception:
        logger.exception("Unexpected error in dashboard overview endpoint")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"code": "DASHBOARD_OVERVIEW_ERROR", "message": "Failed to load dashboard token overview."},
        )


@router.post(
    "/refresh/all",
    response_model=TokenRefreshAllResponse,
    responses={500: {"model": ErrorResponse}},
)
def refresh_all_dashboard_tokens() -> TokenRefreshAllResponse:
    try:
        return service.refresh_all()
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": "DASHBOARD_REFRESH_ALL_ERROR", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=detail)
    except Exception:
        logger.exception("Unexpected error in dashboard refresh-all endpoint")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"code": "DASHBOARD_REFRESH_ALL_ERROR", "message": "Failed to refresh all dashboard token cards."},
        )


@router.post(
    "/refresh",
    response_model=TokenCard,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def refresh_dashboard_token_card(req: TokenRefreshRequest) -> TokenCard:
    symbol = req.symbol.strip().upper() if req.symbol else ""
    if not symbol:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"code": "SYMBOL_REQUIRED", "message": "Field 'symbol' is required."},
        )

    try:
        return service.refresh_one(symbol)
    except LookupError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"code": "TOKEN_NOT_FOUND", "message": "Token configuration not found."},
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": "DASHBOARD_REFRESH_ERROR", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=detail)
    except Exception:
        logger.exception("Unexpected error in dashboard refresh endpoint")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"code": "DASHBOARD_REFRESH_ERROR", "message": "Failed to refresh dashboard token card."},
        )