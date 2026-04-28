from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.wallet_models import ErrorResponse, WalletAnalyzeRequest, WalletChainOptionsResponse, WalletInsightResponse
from app.services.wallet_analysis_service import WalletAnalysisService, WalletAnalysisServiceError
from app.utils.logging_config import get_logger


logger = get_logger("app.api.wallet_analysis")
router = APIRouter(prefix="/api/wallet", tags=["wallet-analysis"])
service = WalletAnalysisService()


@router.get(
    "/chains",
    response_model=WalletChainOptionsResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Wallet Supported Chains",
)
def get_wallet_chain_options() -> WalletChainOptionsResponse | JSONResponse:
    try:
        return WalletChainOptionsResponse(chains=service.get_chain_options())
    except WalletAnalysisServiceError as exc:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})
    except Exception:
        logger.exception("Failed to load wallet chain options")
        return JSONResponse(
            status_code=500,
            content={"code": "WALLET_CHAIN_OPTIONS_ERROR", "message": "Failed to load wallet chain options."},
        )


@router.post(
    "/analyze",
    response_model=WalletInsightResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Analyze Wallet Portfolio",
)
def analyze_wallet(req: WalletAnalyzeRequest) -> WalletInsightResponse | JSONResponse:
    try:
        return service.analyze_wallet(address=req.address, chains=req.chains)
    except WalletAnalysisServiceError as exc:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})
    except Exception:
        logger.exception("Failed to analyze wallet address=%s chains=%s", req.address, req.chains)
        return JSONResponse(
            status_code=500,
            content={"code": "WALLET_ANALYSIS_ERROR", "message": "Failed to analyze wallet portfolio."},
        )
