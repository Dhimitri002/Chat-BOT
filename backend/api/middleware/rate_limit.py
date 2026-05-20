"""
Flora Platform — Rate Limiting Middleware
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import time
import threading


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter.
    For production, use Redis-based rate limiting.
    """

    def __init__(self, app, requests_per_minute: int = 60, burst: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.requests: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        with self._lock:
            # Clean old entries
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if now - t < 60
            ]

            # Check rate limit
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Try again in 60 seconds.",
                    headers={"Retry-After": "60"},
                )

            self.requests[client_ip].append(now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.requests_per_minute - len(self.requests[client_ip]))
        )
        return response
