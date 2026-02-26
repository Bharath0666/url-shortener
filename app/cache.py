"""
Redis caching layer for hot URL lookups.

Strategy:
- On redirect: check Redis first → if miss, query MySQL → populate cache
- On create:   write-through to cache
- On delete:   invalidate cache entry
- Default TTL: 3600 seconds (1 hour)
"""

import time
import logging
import redis
from app.config import Config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton Redis client
# ---------------------------------------------------------------------------
_redis_client: redis.Redis | None = None

CACHE_PREFIX = "url:"
DEFAULT_TTL = 3600  # seconds


def get_redis() -> redis.Redis:
    """Return (and lazily create) the Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            Config.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
        )
    return _redis_client


def _key(short_code: str) -> str:
    return f"{CACHE_PREFIX}{short_code}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_cached_url(short_code: str) -> str | None:
    """Look up a short code in Redis.  Returns original_url or None."""
    try:
        start = time.perf_counter_ns()
        value = get_redis().get(_key(short_code))
        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
        if value:
            logger.info("CACHE HIT  %-10s  (%.2f ms)", short_code, elapsed_ms)
        else:
            logger.info("CACHE MISS %-10s  (%.2f ms)", short_code, elapsed_ms)
        return value
    except redis.RedisError as exc:
        logger.warning("Redis GET failed: %s", exc)
        return None


def set_cached_url(short_code: str, original_url: str, ttl: int = DEFAULT_TTL) -> None:
    """Write a short_code → original_url mapping to Redis."""
    try:
        get_redis().setex(_key(short_code), ttl, original_url)
        logger.debug("CACHE SET  %-10s  ttl=%ds", short_code, ttl)
    except redis.RedisError as exc:
        logger.warning("Redis SET failed: %s", exc)


def invalidate_cache(short_code: str) -> None:
    """Remove a short code from the cache (e.g. on delete)."""
    try:
        get_redis().delete(_key(short_code))
        logger.debug("CACHE DEL  %-10s", short_code)
    except redis.RedisError as exc:
        logger.warning("Redis DEL failed: %s", exc)
