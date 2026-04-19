"""FastAPI application for P2P Marketplace Mini App."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.core.config import get_settings
from api.routers import auth, users, catalog, orders, deals, sellers, reviews, admin, payments, notifications, chat, cart
from api.middleware import LoggingMiddleware, RateLimitMiddleware

settings = get_settings()
logger = logging.getLogger(__name__)

# Redis client for rate limiting
redis_client: Redis | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    global redis_client
    
    logger.info("🚀 Starting FastAPI application...")
    
    # Initialize Redis client for rate limiting
    try:
        redis_client = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Redis connected for rate limiting")
    except Exception as exc:
        logger.warning(f"⚠️ Redis connection failed: {exc}. Rate limiting will be disabled.")
        redis_client = None
    
    yield
    
    # Cleanup
    if redis_client:
        await redis_client.close()
        logger.info("✅ Redis connection closed")
    
    logger.info("👋 Shutting down FastAPI application...")


app = FastAPI(
    title="P2P Marketplace API",
    description="REST API for Telegram Mini App P2P Marketplace",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
cors_origins = ["*"]
if hasattr(settings, 'cors_origins') and settings.cors_origins:
    if settings.cors_origins == "*":
        cors_origins = ["*"]
    else:
        cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]

logger.info(f"🌐 CORS origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware (validates requirement 29.4 - anonymize PII in logs)
app.add_middleware(LoggingMiddleware)

# Rate limiting middleware (validates requirement 29.5 - 10 requests/minute per user)
app.add_middleware(RateLimitMiddleware, redis_client=redis_client, requests_per_minute=10)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "p2p-marketplace-api"}


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "details": None
        }
    )


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(catalog.router, prefix="/api/v1", tags=["Catalog"])
app.include_router(cart.router, prefix="/api/v1/cart", tags=["Cart"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(deals.router, prefix="/api/v1/deals", tags=["Deals"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(sellers.router, prefix="/api/v1/sellers", tags=["Sellers"])
app.include_router(reviews.router, prefix="/api/v1", tags=["Reviews"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(payments.router, prefix="/api/v1", tags=["Payments"])
# Notifications router without prefix for WebSocket to work at /api/v1/ws/notifications
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
