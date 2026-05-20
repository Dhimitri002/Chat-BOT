"""
Flora Platform — Audit Log Middleware
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timezone
import logging

logger = logging.getLogger("flora.audit")

# Actions that should be audited
AUDITABLE_METHODS = {"POST", "PUT", "DELETE", "PATCH"}
AUDITABLE_PATHS = [
    "/api/v1/users",
    "/api/v1/bots",
    "/api/v1/licenses",
    "/api/v1/subscriptions",
    "/api/v1/plans",
]


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that logs sensitive actions for audit purposes."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only audit mutating requests to sensitive paths
        if request.method not in AUDITABLE_METHODS:
            return response

        path = request.url.path
        if not any(path.startswith(audit_path) for audit_path in AUDITABLE_PATHS):
            return response

        # Extract user info if available
        user_id = "anonymous"
        try:
            if hasattr(request.state, "user"):
                user_id = getattr(request.state.user, "id", "anonymous")
        except Exception:
            pass

        logger.info(
            "audit_action",
            extra={
                "user_id": user_id,
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        return response
