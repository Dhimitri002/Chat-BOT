"""
Flora Platform — Security & Observability Middleware

Provides:
- Security headers middleware (HSTS, CSP, X-Frame-Options, etc.)
- Request logging middleware with timing
- Rate limiting middleware (per-IP, per-endpoint)
- CORS configuration helpers
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp

from backend.config import settings

logger = logging.getLogger(__name__)


# ─── Security Headers Middleware ────────────────────────────


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to every response.

    Headers:
        - Strict-Transport-Security (HSTS)
        - X-Content-Type-Options: nosniff
        - X-Frame-Options: DENY
        - X-XSS-Protection: 1; mode=block
        - Referrer-Policy: strict-origin-when-cross-origin
        - Content-Security-Policy (configurable)
        - Permissions-Policy
    """

    def __init__(
        self,
        app: ASGIApp,
        csp: Optional[str] = None,
        enable_hsts: bool = True,
    ):
        super().__init__(app)
        self._csp = csp or "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        self._enable_hsts = enable_hsts

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self._csp

        # Permissions Policy (disable unnecessary browser features)
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # HSTS (only in production with HTTPS)
        if self._enable_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Remove server identification
        if "server" in response.headers:
            del response.headers["server"]

        return response


# ─── Request Logging Middleware ────────────────────────────


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log every request with method, path, status code, duration, and client IP.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        client_ip = self._get_client_ip(request)

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "REQUEST %s %s | %s | ERROR: %s | %.1fms",
                request.method,
                request.url.path,
                client_ip,
                str(exc),
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "REQUEST %s %s | %s | %d | %.1fms",
            request.method,
            request.url.path,
            client_ip,
            response.status_code,
            duration_ms,
        )

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract real client IP considering reverse proxies."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        if request.client:
            return request.client.host
        return "unknown"


# ─── Rate Limiting Middleware ──────────────────────────────


@dataclass
class _RateLimitEntry:
    """Track request count and window start for a client."""
    count: int = 0
    window_start: float = 0.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory rate limiting middleware.

    Limits requests per IP within a sliding window.

    Config:
        - requests_per_window: Max requests allowed per window
        - window_seconds: Window duration in seconds
        - exclude_paths: Paths to skip rate limiting (e.g., health checks)
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_window: int = 100,
        window_seconds: int = 60,
        exclude_paths: Optional[list[str]] = None,
    ):
        super().__init__(app)
        self._max_requests = requests_per_window
        self._window_seconds = window_seconds
        self._exclude_paths = set(exclude_paths or ["/api/v1/health", "/docs", "/redoc", "/openapi.json"])
        self._clients: dict[str, _RateLimitEntry] = defaultdict(_RateLimitEntry)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for excluded paths
        if request.url.path in self._exclude_paths:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.monotonic()

        entry = self._clients[client_ip]

        # Reset window if expired
        if now - entry.window_start >= self._window_seconds:
            entry.count = 0
            entry.window_start = now

        entry.count += 1

        if entry.count > self._max_requests:
            retry_after = int(self._window_seconds - (now - entry.window_start))
            logger.warning(
                "RATE_LIMIT_EXCEEDED %s %s | %s | count=%d",
                request.method,
                request.url.path,
                client_ip,
                entry.count,
            )
            return Response(
                content='{"detail":"Limite de requisições excedido. Tente novamente em breve."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self._max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + retry_after)),
                },
            )

        response = await call_next(request)

        # Add rate limit headers to response
        remaining = max(0, self._max_requests - entry.count)
        response.headers["X-RateLimit-Limit"] = str(self._max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(entry.window_start + self._window_seconds))

        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        if request.client:
            return request.client.host
        return "unknown"


# ─── CORS Configuration Helper ─────────────────────────────


def configure_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware with settings from config.

    Uses settings.CORS_ORIGINS for allowed origins.
    """
    origins = settings.CORS_ORIGINS
    if isinstance(origins, str):
        origins = [o.strip() for o in origins.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "X-Request-ID",
            "X-Device-Fingerprint",
        ],
        expose_headers=[
            "X-Response-Time",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        max_age=600,  # Cache preflight for 10 minutes
    )


# ─── App Setup Helper ──────────────────────────────────────


def setup_security_middleware(app: FastAPI) -> None:
    """
    Register all security middleware on the FastAPI app.

    Order matters — middleware runs in reverse registration order:
        1. Security Headers (outermost)
        2. Rate Limiting
        3. Request Logging
        4. CORS (innermost, runs last on request, first on response)
    """
    # Security headers (outermost — runs first on request, last on response)
    app.add_middleware(
        SecurityHeadersMiddleware,
        enable_hsts=settings.ENVIRONMENT == "production",
    )

    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_window=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # CORS (innermost)
    configure_cors(app)
