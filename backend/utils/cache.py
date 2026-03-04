"""
Sports AI — Redis Cache Utility
Provides async caching with Redis and a decorator for automatic cache management.
"""

import json
import hashlib
from functools import wraps
from typing import Any, Optional
import redis.asyncio as redis
from backend.config.settings import get_settings

settings = get_settings()

_redis_pool: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    return _redis_pool


async def cache_get(key: str) -> Optional[Any]:
    """Retrieve a value from cache."""
    r = await get_redis()
    value = await r.get(key)
    if value is not None:
        return json.loads(value)
    return None


async def cache_set(key: str, value: Any, ttl: int = None) -> None:
    """Store a value in cache with optional TTL."""
    r = await get_redis()
    ttl = ttl or settings.cache_ttl
    await r.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_delete(key: str) -> None:
    """Delete a key from cache."""
    r = await get_redis()
    await r.delete(key)


def cached(prefix: str, ttl: int = None):
    """
    Decorator for caching function results in Redis.

    Usage:
        @cached("match_data", ttl=1800)
        async def get_match(match_id: int):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function args
            key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
            cache_key = f"sai:{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"

            # Try cache first
            result = await cache_get(cache_key)
            if result is not None:
                return result

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            if result is not None:
                await cache_set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


async def close_redis():
    """Close Redis connection pool."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None
