import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dashboard import router as dashboard_router
from app.api.decision import router as decision_router
from app.api.layer56 import router as layer56_router
from app.api.routes import router
from app.config import settings
from app.database import create_tables

app = FastAPI(title=settings.app_name, version="1.0.0")

# CORS — allow frontend on port 8001 to call this backend on port 8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)
app.include_router(decision_router, prefix=settings.api_prefix)
app.include_router(dashboard_router, prefix=settings.api_prefix)
app.include_router(layer56_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup() -> None:
	create_tables()
	os.makedirs("data/temp", exist_ok=True)
