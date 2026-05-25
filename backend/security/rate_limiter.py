"""
Flora Platform — Rate Limiter
==============================
In-memory and Redis-backed rate limiting with sliding window.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_at: float  # Unix timestamp
    retry_after: float = 0.0  # Seconds to wait if denied
    limit: int = 0
    window: int = 0


class RateLimiter(ABC):
    """Abstract base for rate limiters."""

    @abstractmethod
    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Check if a request is allowed under the rate limit."""
        ...

    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset the rate limit for a key."""
        ...


class MemoryRateLimiter(RateLimiter):
    """
    In-memory rate limiter using sliding window.

    Suitable for single-instance deployments.
    Not shared across multiple processes.
    """

    def __init__(self, cleanup_interval: int = 60):
        self._windows: dict[str, list[float]] = {}
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        now = time.time()
        window_start = now - window_seconds

        # Periodic cleanup
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup(now, window_seconds)
            self._last_cleanup = now

        # Get or create window
        if key not in self._windows:
            self._windows[key] = []

        # Remove expired entries
        timestamps = self._windows[key]
        timestamps = [t for t in timestamps if t > window_start]
        self._windows[key] = timestamps

        current_count = len(timestamps)

        if current_count >= limit:
            # Denied
            oldest = min(timestamps) if timestamps else now
            reset_at = oldest + window_seconds
            retry_after = max(0.0, reset_at - now)
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
                retry_after=retry_after,
                limit=limit,
                window=window_seconds,
            )

        # Allowed
        timestamps.append(now)
        remaining = limit - current_count - 1
        reset_at = now + window_seconds

        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=0.0,
            limit=limit,
            window=window_seconds,
        )

    async def reset(self, key: str) -> None:
        self._windows.pop(key, None)

    def _cleanup(self, now: float, max_window: int) -> None:
        """Remove old entries to prevent memory leaks."""
        cutoff = now - max_window * 2
        expired_keys = []
        for key, timestamps in self._windows.items():
            cleaned = [t for t in timestamps if t > cutoff]
            if cleaned:
                self._windows[key] = cleaned
            else:
                expired_keys.append(key)
        for key in expired_keys:
            del self._windows[key]

    def get_stats(self) -> dict:
        """Return stats for monitoring."""
        return {
            "tracked_keys": len(self._windows),
            "total_requests": sum(len(v) for v in self._windows.values()),
        }


class RedisRateLimiter(RateLimiter):
    """
    Redis-backed rate limiter using sorted sets.

    Suitable for multi-instance deployments.
    Uses sliding window algorithm with ZREMRANGEBYSCORE.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self._redis_url = redis_url
        self._redis = None
        self._connected = False

    async def _get_redis(self):
        """Lazy Redis connection."""
        if self._redis is not None:
            return self._redis

        try:
            import redis.asyncio as redis
            self._redis = redis.from_url(self._redis_url, decode_responses=True)
            await self._redis.ping()
            self._connected = True
            logger.info("RedisRateLimiter: connected to Redis")
            return self._redis
        except Exception as e:
            logger.warning(f"RedisRateLimiter: Redis unavailable, falling back to memory: {e}")
            self._connected = False
            raise

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        try:
            r = await self._get_redis()
        except Exception:
            # Fallback to memory limiter if Redis is down
            fallback = MemoryRateLimiter()
            return await fallback.check(key, limit, window_seconds)

        now = time.time()
        window_start = now - window_seconds
        redis_key = f"ratelimit:{key}"

        pipe = r.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zadd(redis_key, {f"{now}:{id(now)}": now})
        pipe.zcard(redis_key)
        pipe.expire(redis_key, window_seconds * 2)
        results = await pipe.execute()

        current_count = results[2]

        if current_count > limit:
            # Remove the request we just added
            await r.zrem(redis_key, f"{now}:{id(now)}")
            # Find oldest for retry_after
            oldest = await r.zrange(redis_key, 0, 0, withscores=True)
            reset_at = oldest[0][1] + window_seconds if oldest else now + window_seconds
            retry_after = max(0.0, reset_at - now)

            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
                retry_after=retry_after,
                limit=limit,
                window=window_seconds,
            )

        remaining = limit - current_count
        reset_at = now + window_seconds

        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=0.0,
            limit=limit,
            window=window_seconds,
        )

    async def reset(self, key: str) -> None:
        try:
            r = await self._get_redis()
            await r.delete(f"ratelimit:{key}")
        except Exception as e:
            logger.warning(f"RedisRateLimiter.reset failed for {key}: {e}")

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None
