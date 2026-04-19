"""Redis cache service for catalog data."""
from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service with 5-minute TTL for catalog data."""
    
    CATALOG_TTL = 300  # 5 minutes in seconds
    
    def __init__(self, redis_url: str):
        """Initialize Redis connection."""
        self.redis_url = redis_url
        self._redis: redis.Redis | None = None
    
    async def connect(self):
        """Connect to Redis."""
        if self._redis is None:
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if not self._redis:
            await self.connect()
        
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = CATALOG_TTL):
        """Set value in cache with TTL."""
        if not self._redis:
            await self.connect()
        
        try:
            serialized = json.dumps(value, default=str)
            await self._redis.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
    
    async def delete(self, key: str):
        """Delete key from cache."""
        if not self._redis:
            await self.connect()
        
        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        if not self._redis:
            await self.connect()
        
        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self._redis.delete(*keys)
                logger.info(f"Deleted {len(keys)} keys matching pattern {pattern}")
        except Exception as e:
            logger.error(f"Redis DELETE_PATTERN error for pattern {pattern}: {e}")


# Global cache service instance
_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    """Get or create cache service instance."""
    global _cache_service
    if _cache_service is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _cache_service = CacheService(redis_url)
    return _cache_service
