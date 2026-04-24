from fastapi import FastAPI

from app.api.dashboard_tokens import router as dashboard_tokens_router


app = FastAPI(title="Blockchain MPC Dashboard Demo", version="0.1.0")
app.include_router(dashboard_tokens_router)

