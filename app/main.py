from fastapi import FastAPI

from app.api.dashboard_tokens import router as dashboard_tokens_router
from app.api.token_detail import router as token_detail_router


app = FastAPI(title="Blockchain MPC Dashboard Demo", version="0.1.0")
app.include_router(dashboard_tokens_router)
app.include_router(token_detail_router)
