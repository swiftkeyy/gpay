"""Rate limiting middleware for FastAPI application."""
import logging
import time
from typing import Callable

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests per user.
    
    Implements a sliding window rate limiter using Redis.
    Default limit: 10 requests per minute per user (as per requirement 29.5).
    """
    
    def __init__(self, app, redis_client: Redis | None = None, requests_per_minute: int = 10):
        """Initialize rate limiter.
        
        Args:
            app: FastAPI application
            redis_client: Redis client for storing rate limit data
            requests_per_minute: Maximum requests allowed per minute per user
        """
        super().__init__(app)
        self.redis_client = redis_client
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        # Skip rate limiting for health check and docs endpoints
        if request.url.path in ["/health", "/api/docs", "/api/redoc", "/api/openapi.json"]:
            return await call_next(request)
        
        # Skip if Redis is not available (graceful degradation)
        if not self.redis_client:
            logger.warning("Rate limiting disabled: Redis client not available")
            return await call_next(request)
        
        # Extract user identifier (IP address or user ID from auth)
        user_id = await self._get_user_identifier(request)
        
        # Check rate limit
        try:
            is_allowed = await self._check_rate_limit(user_id)
            
            if not is_allowed:
                logger.warning(f"Rate limit exceeded for user: {user_id}")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": self.window_seconds
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            remaining = await self._get_remaining_requests(user_id)
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window_seconds)
            
            return response
            
        except HTTPException:
            raise
        except Exception as exc:
            # Log error but don't block request if rate limiting fails
            logger.error(f"Rate limiting error: {exc}", exc_info=True)
            return await call_next(request)
    
    async def _get_user_identifier(self, request: Request) -> str:
        """Extract user identifier from request.
        
        Args:
            request: HTTP request
            
        Returns:
            User identifier (user ID or IP address)
        """
        # Try to get user ID from request state (set by auth middleware)
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # Fall back to IP address
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    async def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        key = f"rate_limit:{user_id}"
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        try:
            # Use Redis sorted set for sliding window
            # Remove old entries outside the window
            await self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            request_count = await self.redis_client.zcard(key)
            
            if request_count >= self.requests_per_minute:
                return False
            
            # Add current request
            await self.redis_client.zadd(key, {str(current_time): current_time})
            
            # Set expiration on key
            await self.redis_client.expire(key, self.window_seconds * 2)
            
            return True
            
        except Exception as exc:
            logger.error(f"Redis error in rate limiting: {exc}")
            # Allow request if Redis fails (fail open)
            return True
    
    async def _get_remaining_requests(self, user_id: str) -> int:
        """Get remaining requests for user in current window.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of remaining requests
        """
        key = f"rate_limit:{user_id}"
        
        try:
            request_count = await self.redis_client.zcard(key)
            remaining = max(0, self.requests_per_minute - request_count)
            return remaining
        except Exception:
            return self.requests_per_minute
