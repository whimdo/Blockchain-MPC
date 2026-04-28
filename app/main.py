from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.ai_chat import router as ai_chat_router
from app.api.auth import router as auth_router
from app.api.dao_proposal import router as dao_proposal_router
from app.api.dashboard_tokens import router as dashboard_tokens_router
from app.api.token_detail import router as token_detail_router
from app.api.wallet_analysis import router as wallet_analysis_router
from app.services.mcp_client_manager import mcp_client_manager
from app.utils.logging_config import get_logger


logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await mcp_client_manager.start()
    except Exception:
        logger.exception("Failed to start MCP singleton client during FastAPI startup")

    try:
        yield
    finally:
        await mcp_client_manager.cleanup()


app = FastAPI(title="Blockchain MPC Dashboard Demo", version="0.1.0", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory="app/assets"), name="assets")
app.include_router(auth_router)
app.include_router(dashboard_tokens_router)
app.include_router(token_detail_router)
app.include_router(dao_proposal_router)
app.include_router(ai_chat_router)
app.include_router(wallet_analysis_router)
