from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers.api import router as api_router

settings = get_settings()

app = FastAPI(
    title="Blinkit Feedback Intelligence API",
    description="AI-powered Play Store review insights for Blinkit Product Managers",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def root() -> dict:
    return {
        "name": "Blinkit Feedback Intelligence",
        "docs": "/docs",
        "health": "/api/health",
    }
