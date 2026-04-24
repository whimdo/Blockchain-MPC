from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.token_detail_demo_service import TokenDetailDemoService
from app.utils.logging_config import get_logger


logger = get_logger("app.api.token_detail_demo")
router = APIRouter(prefix="/api/dashboard/tokens", tags=["dashboard-token-detail-demo"])
service = TokenDetailDemoService()


class TokenRefreshRequest(BaseModel):
    symbol: str = Field(..., description="Token symbol, e.g. ETH")


def _json_error(code: int, err_code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=code, content={"code": err_code, "message": message})


@router.get("/detail")
def get_token_detail(symbol: str = Query(..., description="Token symbol, e.g. BTC")) -> Any:
    token_symbol = (symbol or "").strip().upper()
    if not token_symbol:
        return _json_error(400, "SYMBOL_REQUIRED", "Query parameter 'symbol' is required.")

    try:
        return service.build_detail(token_symbol)
    except LookupError:
        return _json_error(404, "TOKEN_NOT_FOUND", "Token configuration not found.")
    except Exception:
        logger.exception("Failed to load token detail symbol=%s", token_symbol)
        return _json_error(500, "TOKEN_DETAIL_ERROR", "Failed to load token detail.")


@router.get("/chart")
def get_token_chart(
    symbol: str = Query(..., description="Token symbol, e.g. BTC"),
    range: str = Query("7d", description="1d|7d|1m|3m|1y"),
    interval: str | None = Query(default=None, description="15m|1h|4h|1d|1w"),
) -> Any:
    token_symbol = (symbol or "").strip().upper()
    if not token_symbol:
        return _json_error(400, "SYMBOL_REQUIRED", "Query parameter 'symbol' is required.")

    try:
        return service.build_chart(token_symbol, chart_range=range, interval=interval)
    except LookupError:
        return _json_error(404, "TOKEN_NOT_FOUND", "Token configuration not found.")
    except Exception:
        logger.exception("Failed to load token chart symbol=%s", token_symbol)
        return _json_error(500, "TOKEN_CHART_ERROR", "Failed to load token chart.")


@router.post("/refresh")
def refresh_token_detail(req: TokenRefreshRequest) -> Any:
    token_symbol = (req.symbol or "").strip().upper()
    if not token_symbol:
        return _json_error(400, "SYMBOL_REQUIRED", "Field 'symbol' is required.")

    try:
        return service.build_refresh(token_symbol)
    except LookupError:
        return _json_error(404, "TOKEN_NOT_FOUND", "Token configuration not found.")
    except Exception:
        logger.exception("Failed to refresh token detail symbol=%s", token_symbol)
        return _json_error(500, "TOKEN_REFRESH_ERROR", "Failed to refresh token detail.")
