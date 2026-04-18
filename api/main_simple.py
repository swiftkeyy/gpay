"""Simplified FastAPI application for Mini App."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from api.routers_simple import auth, games, categories, products, lots

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    logger.info("🚀 Starting FastAPI application...")
    yield
    logger.info("👋 Shutting down FastAPI application...")


app = FastAPI(
    title="Game Pay API",
    description="REST API for Game Pay - Telegram Mini App P2P Marketplace",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажи конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "game-pay-api"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Game Pay API",
        "docs": "/api/docs",
        "health": "/health"
    }


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(games.router, prefix="/api/v1", tags=["Games"])
app.include_router(categories.router, prefix="/api/v1", tags=["Categories"])
app.include_router(products.router, prefix="/api/v1", tags=["Products"])
app.include_router(lots.router, prefix="/api/v1", tags=["Lots"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
