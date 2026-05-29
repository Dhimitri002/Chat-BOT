"""
Flora Platform — Audit Logging
===============================
Structured audit logging for security events, data access,
and administrative actions.
"""

import functools
import json
import logging
import time
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger("audit")


class AuditAction(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    REGISTER = "register"
    PASSWORD_CHANGE = "password_change"
    TOKEN_REFRESH = "token_refresh"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    LICENSE_GENERATE = "license_generate"
    LICENSE_REVOKE = "license_revoke"
    LICENSE_VALIDATE = "license_validate"
    WHATSAPP_CONNECT = "whatsapp_connect"
    WHATSAPP_DISCONNECT = "whatsapp_disconnect"
    SETTINGS_CHANGE = "settings_change"
    MFA_ENABLE = "mfa_enable"
    MFA_DISABLE = "mfa_disable"


class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(str, Enum):
    AUTH = "auth"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    LICENSE = "license"
    SECURITY = "security"
    ADMIN = "admin"
    SYSTEM = "system"
    API = "api"
    BILLING = "billing"


class AuditLogger:
    """
    Structured audit logger for security-relevant events.

    Logs events with:
    - Timestamp (UTC)
    - Category and action
    - Actor (user/system)
    - Target (resource affected)
    - Severity
    - Details (structured data)
    """

    def __init__(self, log_file: Optional[str] = None):
        self._log_file = log_file
        self._events: list[dict] = []

        # Set up dedicated audit logger
        self._audit_logger = logging.getLogger("flora.audit")
        if log_file:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(
                logging.Formatter("%(asctime)s | %(message)s")
            )
            self._audit_logger.addHandler(handler)
            self._audit_logger.setLevel(logging.INFO)

    def log(
        self,
        action: str,
        category: AuditCategory = AuditCategory.SYSTEM,
        severity: AuditSeverity = AuditSeverity.INFO,
        actor: str = "system",
        target: str = "",
        details: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> dict:
        """
        Log an audit event.

        Returns the event dict for testing/verification.
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "category": category.value,
            "severity": severity.value,
            "actor": actor,
            "target": target,
            "details": details or {},
        }
        if error:
            event["error"] = error

        self._events.append(event)

        # Log to file/logger
        log_msg = json.dumps(event, default=str)
        if severity in (AuditSeverity.ERROR, AuditSeverity.CRITICAL):
            self._audit_logger.error(log_msg)
        elif severity == AuditSeverity.WARNING:
            self._audit_logger.warning(log_msg)
        else:
            self._audit_logger.info(log_msg)

        return event

    def log_auth(
        self,
        action: str,
        user_id: str = "",
        success: bool = True,
        details: Optional[dict] = None,
    ) -> dict:
        """Log authentication events."""
        return self.log(
            action=action,
            category=AuditCategory.AUTH,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            actor=user_id or "anonymous",
            target="auth",
            details={**(details or {}), "success": success},
        )

    def log_data_access(
        self,
        action: str,
        user_id: str,
        resource: str,
        resource_id: str = "",
        details: Optional[dict] = None,
    ) -> dict:
        """Log data access events."""
        return self.log(
            action=action,
            category=AuditCategory.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            actor=user_id,
            target=f"{resource}:{resource_id}",
            details=details,
        )

    def log_security(
        self,
        action: str,
        severity: AuditSeverity = AuditSeverity.WARNING,
        actor: str = "system",
        target: str = "",
        details: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> dict:
        """Log security events."""
        return self.log(
            action=action,
            category=AuditCategory.SECURITY,
            severity=severity,
            actor=actor,
            target=target,
            details=details,
            error=error,
        )

    def log_admin(
        self,
        action: str,
        admin_id: str,
        target: str = "",
        details: Optional[dict] = None,
    ) -> dict:
        """Log administrative actions."""
        return self.log(
            action=action,
            category=AuditCategory.ADMIN,
            severity=AuditSeverity.INFO,
            actor=admin_id,
            target=target,
            details=details,
        )

    def get_events(
        self,
        category: Optional[AuditCategory] = None,
        severity: Optional[AuditSeverity] = None,
        actor: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Query logged events with optional filters."""
        events = self._events

        if category:
            events = [e for e in events if e["category"] == category.value]
        if severity:
            events = [e for e in events if e["severity"] == severity.value]
        if actor:
            events = [e for e in events if e["actor"] == actor]

        return events[-limit:]

    def clear(self) -> None:
        """Clear in-memory events."""
        self._events.clear()


# Global singleton
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(log_file: Optional[str] = None) -> AuditLogger:
    """Get or create the global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(log_file=log_file)
    return _audit_logger


def audit_log(
    action: str,
    category: AuditCategory = AuditCategory.SYSTEM,
    severity: AuditSeverity = AuditSeverity.INFO,
    actor: str = "system",
    target: str = "",
    details: Optional[dict] = None,
):
    """
    Decorator to automatically audit-log function calls.

    Usage:
        @audit_log("user.login", category=AuditCategory.AUTH)
        async def login(username, password):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            alog = get_audit_logger()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start
                alog.log(
                    action=action,
                    category=category,
                    severity=severity,
                    actor=actor,
                    target=target or func.__name__,
                    details={**(details or {}), "elapsed_ms": round(elapsed * 1000, 2)},
                )
                return result
            except Exception as e:
                elapsed = time.time() - start
                alog.log(
                    action=action,
                    category=category,
                    severity=AuditSeverity.ERROR,
                    actor=actor,
                    target=target or func.__name__,
                    details={**(details or {}), "elapsed_ms": round(elapsed * 1000, 2)},
                    error=str(e),
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            alog = get_audit_logger()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                alog.log(
                    action=action,
                    category=category,
                    severity=severity,
                    actor=actor,
                    target=target or func.__name__,
                    details={**(details or {}), "elapsed_ms": round(elapsed * 1000, 2)},
                )
                return result
            except Exception as e:
                elapsed = time.time() - start
                alog.log(
                    action=action,
                    category=category,
                    severity=AuditSeverity.ERROR,
                    actor=actor,
                    target=target or func.__name__,
                    details={**(details or {}), "elapsed_ms": round(elapsed * 1000, 2)},
                    error=str(e),
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
