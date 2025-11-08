"""Redis client management."""

from __future__ import annotations

from typing import Optional

import redis.asyncio as redis

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Return a Redis client, configuring it on first access. Returns None if Redis is not configured."""

    global _redis
    if _redis is not None:
        return _redis

    settings = get_settings()
    if not settings.redis_url:
        logger.warning("redis.not_configured", msg="REDIS_URL not set, continuing without Redis")
        return None

    _redis = redis.from_url(str(settings.redis_url), decode_responses=False)
    return _redis


async def init_redis() -> None:
    """Verify Redis connectivity during application startup."""

    client = get_redis()
    if client is None:
        logger.warning("redis.skipped", msg="Redis not configured, skipping initialization")
        return
    
    try:
        await client.ping()
        logger.info("redis.connected")
    except Exception:
        logger.exception("redis.connection_failed")
        raise




