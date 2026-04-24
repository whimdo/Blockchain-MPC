from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.token_detail_models import (
    TokenAISummaryRequest,
    TokenAISummaryResponse,
    TokenChartRequest,
    TokenChartSummary,
    TokenChartResponse,
    TokenDetailRequest,
    TokenDetailResponse,
)
from app.services.ai_service import AIService
from app.services.token_detail_service import TokenDetailService
from app.utils.logging_config import get_logger


logger = get_logger("app.api.token_detail")
router = APIRouter(prefix="/api/dashboard/tokens", tags=["dashboard-token-detail"])
service = TokenDetailService()
ai_service = AIService()


def _json_error(code: int, err_code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=code, content={"code": err_code, "message": message})


@router.post(
    "/detail",
    response_model=TokenDetailResponse,
    summary="获取 Token 详情",
    description="通过请求体传入参数，返回 TokenDetailResponse。",
)
def get_token_detail(req: TokenDetailRequest) -> Any:
    token_symbol = (req.symbol or "").strip().upper()
    if not token_symbol:
        return _json_error(400, "SYMBOL_REQUIRED", "Field 'symbol' is required.")

    try:
        return service.build_detail(
            symbol=token_symbol,
            include_chart=req.include_chart,
            chart_range=req.chart_range,
            chart_interval=req.chart_interval,
        )
    except LookupError:
        return _json_error(404, "TOKEN_NOT_FOUND", "Token configuration not found.")
    except Exception:
        logger.exception("Failed to load token detail symbol=%s", token_symbol)
        return _json_error(500, "TOKEN_DETAIL_ERROR", "Failed to load token detail.")


@router.post(
    "/chart",
    response_model=TokenChartResponse,
    summary="获取 Token 图表",
    description="通过请求体传入 symbol、range、interval 等参数，返回 TokenChartResponse。",
)
def get_token_chart(req: TokenChartRequest) -> Any:
    token_symbol = (req.symbol or "").strip().upper()
    if not token_symbol:
        return _json_error(400, "SYMBOL_REQUIRED", "Field 'symbol' is required.")

    try:
        return service.build_chart(token_symbol, chart_range=req.range, interval=req.interval)
    except LookupError:
        return _json_error(404, "TOKEN_NOT_FOUND", "Token configuration not found.")
    except Exception:
        logger.exception("Failed to load token chart symbol=%s", token_symbol)
        return _json_error(500, "TOKEN_CHART_ERROR", "Failed to load token chart.")


@router.post(
    "/ai-summary",
    response_model=TokenAISummaryResponse,
    summary="获取 Token AI 总结",
    description="通过请求体传入 symbol 和可选的 chart_summary，返回结构化 TokenAISummaryResponse。",
)
def get_token_ai_summary(req: TokenAISummaryRequest) -> Any:
    token_symbol = (req.symbol or "").strip().upper()
    if not token_symbol:
        return _json_error(400, "SYMBOL_REQUIRED", "Field 'symbol' is required.")

    try:
        chart_summary = req.chart_summary
        if chart_summary is None:
            chart_resp = service.build_chart(token_symbol, chart_range="7d", interval=None)
            chart_summary = chart_resp.summary or TokenChartSummary()

        summary = ai_service.generate_token_ai_summary(
            symbol=token_symbol,
            chart_summary=chart_summary,
        )
        return TokenAISummaryResponse(symbol=token_symbol, summary=summary)
    except LookupError:
        return _json_error(404, "TOKEN_NOT_FOUND", "Token configuration not found.")
    except Exception:
        logger.exception("Failed to generate token ai summary symbol=%s", token_symbol)
        return _json_error(500, "TOKEN_AI_SUMMARY_ERROR", "Failed to generate token ai summary.")
