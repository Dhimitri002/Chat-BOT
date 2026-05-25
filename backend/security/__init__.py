"""
Flora Platform — Security Package
==================================
Módulos de segurança para criptografia, licenciamento, anti-clone,
audit logging e rate limiting.
"""

from backend.security.crypto import CryptoManager, LicenseSigner
from backend.security.license_manager import LicenseManager
from backend.security.anti_clone import AntiClone
from backend.security.audit import AuditLogger, audit_log
from backend.security.rate_limiter import RateLimiter, MemoryRateLimiter, RedisRateLimiter
from backend.security.middleware import RateLimitMiddleware

__all__ = [
    "CryptoManager",
    "LicenseSigner",
    "LicenseManager",
    "AntiClone",
    "AuditLogger",
    "audit_log",
    "RateLimiter",
    "MemoryRateLimiter",
    "RedisRateLimiter",
    "RateLimitMiddleware",
]
