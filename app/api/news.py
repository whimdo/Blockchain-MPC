from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.models.news_models import ErrorResponse, NewsLatestResponse, NewsSyncResponse
from app.services.news_service import NewsService, NewsServiceError
from app.utils.logging_config import get_logger


logger = get_logger("app.api.news")
router = APIRouter(prefix="/api/news", tags=["news"])
service = NewsService()


@router.get(
    "/latest",
    response_model=NewsLatestResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Latest News",
)
def get_latest_news(
    limit: int = Query(default=24, ge=1, le=100),
    category: str | None = Query(default=None),
    symbol: str | None = Query(default=None),
) -> NewsLatestResponse | JSONResponse:
    try:
        return service.latest(limit=limit, category=category, symbol=symbol)
    except NewsServiceError as exc:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})
    except Exception:
        logger.exception("Failed to load latest news")
        return JSONResponse(status_code=500, content={"code": "NEWS_LATEST_ERROR", "message": "Failed to load latest news."})


@router.post(
    "/sync",
    response_model=NewsSyncResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Sync CoinDesk RSS News",
)
def sync_news(limit: int = Query(default=50, ge=1, le=100)) -> NewsSyncResponse | JSONResponse:
    try:
        return service.sync(limit=limit)
    except NewsServiceError as exc:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})
    except Exception:
        logger.exception("Failed to sync news")
        return JSONResponse(status_code=500, content={"code": "NEWS_SYNC_ERROR", "message": "Failed to sync news."})
