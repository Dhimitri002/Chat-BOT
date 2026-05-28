"""
Flora Platform — Metrics Middleware
=====================================

FastAPI middleware that collects request/response metrics
and integrates with monitoring.metrics.
"""
from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from monitoring.metrics import request_metrics


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collects request duration, status codes, and counts."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)

        request_metrics.record(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
