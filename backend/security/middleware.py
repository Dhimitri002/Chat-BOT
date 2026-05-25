"""
Flora Platform — Rate Limiting Middleware
==========================================
Starlette/FastAPI middleware for global and per-endpoint rate limiting.
"""

import logging
import time
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.security.rate_limiter import MemoryRateLimiter, RateLimiter

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware for FastAPI.

    Applies a default rate limit to all requests.
    Can be overridden per-route using dependencies.

    Config:
        default_limit: Max requests per window
        window_seconds: Time window in seconds
        exclude_paths: Paths to skip rate limiting
        key_func: Function to extract client key from request
    """

    def __init__(
        self,
        app,
        rate_limiter: Optional[RateLimiter] = None,
        default_limit: int = 100,
        window_seconds: int = 60,
        exclude_paths: Optional[list] = None,
        key_func=None,
    ):
        super().__init__(app)
        self._limiter = rate_limiter or MemoryRateLimiter()
        self._default_limit = default_limit
        self._window_seconds = window_seconds
        self._exclude_paths = set(exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"])
        self._key_func = key_func or self._default_key_func

    @staticmethod
    def _default_key_func(request: Request) -> str:
        """
        Extract a client identifier from the request.

        Uses X-Forwarded-For header if behind proxy,
        falls back to client IP.
        """
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        # Include path for per-endpoint limits
        return f"{ip}:{request.url.path}"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with rate limiting."""
        path = request.url.path

        # Skip excluded paths
        if path in self._exclude_paths:
            return await call_next(request)

        # Get client key
        key = self._key_func(request)

        # Check rate limit
        result = await self._limiter.check(key, self._default_limit, self._window_seconds)

        # Build response
        if not result.allowed:
            logger.warning(f"Rate limit exceeded: {key}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Muitas requisições. Tente novamente em instantes.",
                    "retry_after": round(result.retry_after, 1),
                },
                headers={
                    "Retry-After": str(int(result.retry_after) + 1),
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(result.reset_at)),
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, result.remaining))
        response.headers["X-RateLimit-Reset"] = str(int(result.reset_at))

        return response


class EndpointRateLimiter:
    """
    Per-endpoint rate limiter for use as a FastAPI dependency.

    Usage:
        @router.post("/auth/login")
        async def login(
            data: LoginRequest,
            _: None = Depends(EndpointRateLimiter(limit=5, window_seconds=300)),
        ):
            ...
    """

    def __init__(
        self,
        limit: int = 10,
        window_seconds: int = 60,
        key_func=None,
        limiter: Optional[RateLimiter] = None,
    ):
        self._limit = limit
        self._window = window_seconds
        self._key_func = key_func or self._default_key
        self._limiter = limiter or MemoryRateLimiter()

    @staticmethod
    def _default_key(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        ip = forwarded.split(",")[0].strip() if forwarded else (
            request.client.host if request.client else "unknown"
        )
        return f"endpoint:{ip}:{request.url.path}"

    async def __call__(self, request: Request) -> None:
        key = self._key_func(request)
        result = await self._limiter.check(key, self._limit, self._window)

        if not result.allowed:
            raise RateLimitExceeded(result)


class RateLimitExceeded(Exception):
    """Raised when a rate limit is exceeded in endpoint-level limiting."""

    def __init__(self, result):
        self.result = result
        self.retry_after = result.retry_after
        super().__init__(f"Rate limit exceeded, retry after {result.retry_after}s")
