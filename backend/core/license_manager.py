"""
Flora Platform — Core License Manager
======================================
Server-side license validation, plan enforcement,
and feature gating for the backend API.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from backend.config import settings
from backend.models.license import License
from backend.models.plan import Plan

logger = logging.getLogger(__name__)


class LicenseCheckResult(str, Enum):
    VALID = "valid"
    EXPIRED = "expired"
    NOT_FOUND = "not_found"
    LIMIT_EXCEEDED = "limit_exceeded"
    FEATURE_NOT_AVAILABLE = "feature_not_available"
    HARDWARE_MISMATCH = "hardware_mismatch"
    SUSPENDED = "suspended"


@dataclass
class FeatureGate:
    """Defines a feature gate with plan requirements."""
    feature_key: str
    name: str
    description: str
    min_plan_level: int = 1  # Plan level required (1=free, 2=starter, etc.)


# ─── Plan Feature Matrix ───────────────────────────────────────────

PLAN_LIMITS = {
    "free": {
        "level": 1,
        "max_bots": 1,
        "max_messages_per_day": 50,
        "max_users": 1,
        "features": ["basic_chat", "whatsapp_connect"],
    },
    "starter": {
        "level": 2,
        "max_bots": 2,
        "max_messages_per_day": 500,
        "max_users": 3,
        "features": ["basic_chat", "whatsapp_connect", "custom_commands", "analytics_basic"],
    },
    "pro": {
        "level": 3,
        "max_bots": 5,
        "max_messages_per_day": 5000,
        "max_users": 10,
        "features": [
            "basic_chat", "whatsapp_connect", "custom_commands",
            "analytics_basic", "analytics_advanced", "multi_language",
            "api_access", "custom_personality",
        ],
    },
    "business": {
        "level": 4,
        "max_bots": 15,
        "max_messages_per_day": 25000,
        "max_users": 50,
        "features": [
            "basic_chat", "whatsapp_connect", "custom_commands",
            "analytics_basic", "analytics_advanced", "multi_language",
            "api_access", "custom_personality", "priority_support",
            "white_label", "webhooks",
        ],
    },
    "enterprise": {
        "level": 5,
        "max_bots": 100,
        "max_messages_per_day": 100000,
        "max_users": 500,
        "features": [
            "basic_chat", "whatsapp_connect", "custom_commands",
            "analytics_basic", "analytics_advanced", "multi_language",
            "api_access", "custom_personality", "priority_support",
            "white_label", "webhooks", "dedicated_instance",
            "custom_llm", "sla_guarantee",
        ],
    },
}


class CoreLicenseManager:
    """
    Server-side license validation and feature gating.

    Handles:
    - License creation and renewal
    - Plan enforcement (bots, messages, features)
    - Usage tracking and limits
    - Grace period handling
    """

    def __init__(self):
        self._usage_cache: dict[str, dict] = {}
        logger.info("CoreLicenseManager initialized")

    # ─── License CRUD ─────────────────────────────────────────────

    async def validate_license(
        self,
        db,
        user_id: str,
    ) -> LicenseCheckResult:
        """
        Validate a user's license.

        Checks:
        1. License exists
        2. Not expired
        3. Not suspended
        4. Plan is active
        """
        try:
            license_obj = await db.query(License).filter(
                License.user_id == user_id,
                License.is_active == True,
            ).first()

            if not license_obj:
                return LicenseCheckResult.NOT_FOUND

            if license_obj.status == "suspended":
                return LicenseCheckResult.SUSPENDED

            if license_obj.is_expired:
                # Check grace period
                if license_obj.is_in_grace_period:
                    logger.info(f"User {user_id} in grace period")
                    return LicenseCheckResult.VALID
                return LicenseCheckResult.EXPIRED

            return LicenseCheckResult.VALID

        except Exception as e:
            logger.error(f"License validation error for user {user_id}: {e}")
            return LicenseCheckResult.NOT_FOUND

    async def create_license(
        self,
        db,
        user_id: str,
        plan_id: str,
        duration_days: int = 30,
        is_trial: bool = False,
    ) -> License:
        """Create a new license for a user."""
        from datetime import timedelta

        license_obj = License(
            user_id=user_id,
            plan_id=plan_id,
            issued_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=duration_days),
            is_trial=is_trial,
            is_active=True,
            status="active",
        )

        db.add(license_obj)
        await db.commit()
        await db.refresh(license_obj)

        logger.info(f"License created: user={user_id} plan={plan_id} expiry={license_obj.expires_at}")
        return license_obj

    async def renew_license(
        self,
        db,
        user_id: str,
        additional_days: int = 30,
    ) -> Optional[License]:
        """Renew a user's license."""
        license_obj = await db.query(License).filter(
            License.user_id == user_id,
            License.is_active == True,
        ).first()

        if not license_obj:
            return None

        from datetime import timedelta
        current_expiry = license_obj.expires_at
        now = datetime.now(timezone.utc)

        # If expired, start from now; otherwise extend
        if current_expiry < now:
            license_obj.expires_at = now + timedelta(days=additional_days)
        else:
            license_obj.expires_at = current_expiry + timedelta(days=additional_days)

        license_obj.status = "active"
        await db.commit()
        await db.refresh(license_obj)

        logger.info(f"License renewed: user={user_id} new_expiry={license_obj.expires_at}")
        return license_obj

    async def suspend_license(self, db, user_id: str, reason: str = "") -> bool:
        """Suspend a user's license."""
        license_obj = await db.query(License).filter(
            License.user_id == user_id,
            License.is_active == True,
        ).first()

        if not license_obj:
            return False

        license_obj.status = "suspended"
        await db.commit()

        logger.warning(f"License suspended: user={user_id} reason={reason}")
        return True

    async def deactivate_license(self, db, user_id: str) -> bool:
        """Deactivate a user's license."""
        license_obj = await db.query(License).filter(
            License.user_id == user_id,
        ).first()

        if not license_obj:
            return False

        license_obj.is_active = False
        license_obj.status = "inactive"
        await db.commit()

        logger.info(f"License deactivated: user={user_id}")
        return True

    # ─── Plan & Feature Checks ────────────────────────────────────

    def get_plan_limits(self, plan_id: str) -> dict:
        """Get limits for a plan."""
        return PLAN_LIMITS.get(plan_id, PLAN_LIMITS["free"])

    def check_feature_access(self, plan_id: str, feature_key: str) -> bool:
        """Check if a plan has access to a feature."""
        limits = self.get_plan_limits(plan_id)
        return feature_key in limits.get("features", [])

    async def check_usage_limit(
        self,
        db,
        user_id: str,
        limit_type: str,  # "bots", "messages", "users"
        current_count: int,
    ) -> bool:
        """Check if user is within their plan's usage limit."""
        try:
            license_obj = await db.query(License).filter(
                License.user_id == user_id,
                License.is_active == True,
            ).first()

            if not license_obj:
                return False

            plan_id = license_obj.plan_id
            limits = self.get_plan_limits(plan_id)

            max_values = {
                "bots": limits.get("max_bots", 1),
                "messages": limits.get("max_messages_per_day", 50),
                "users": limits.get("max_users", 1),
            }

            max_value = max_values.get(limit_type, 0)
            return current_count < max_value

        except Exception as e:
            logger.error(f"Usage limit check error: {e}")
            return False

    def get_plan_level(self, plan_id: str) -> int:
        """Get the level of a plan (higher = more features)."""
        limits = self.get_plan_limits(plan_id)
        return limits.get("level", 1)

    def can_use_feature(self, plan_id: str, feature_key: str) -> bool:
        """Check if a plan tier includes a specific feature."""
        return self.check_feature_access(plan_id, feature_key)

    # ─── Usage Tracking ───────────────────────────────────────────

    def _get_usage_key(self, user_id: str, date: str = None) -> str:
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{user_id}:{date}"

    async def track_usage(
        self,
        user_id: str,
        usage_type: str,  # "message", "api_call", "bot_action"
        count: int = 1,
    ) -> dict:
        """Track daily usage for a user."""
        key = self._get_usage_key(user_id)

        if key not in self._usage_cache:
            self._usage_cache[key] = {
                "messages": 0,
                "api_calls": 0,
                "bot_actions": 0,
            }

        type_key = f"{usage_type}s" if not usage_type.endswith("s") else usage_type
        if type_key not in self._usage_cache[key]:
            self._usage_cache[key][type_key] = 0
        self._usage_cache[key][type_key] += count

        return self._usage_cache[key]

    def get_usage(self, user_id: str, date: str = None) -> dict:
        """Get usage for a user on a given date."""
        key = self._get_usage_key(user_id, date)
        return self._usage_cache.get(key, {
            "messages": 0,
            "api_calls": 0,
            "bot_actions": 0,
        })

    def reset_usage(self, user_id: str = None) -> None:
        """Reset usage tracking."""
        if user_id:
            keys_to_remove = [k for k in self._usage_cache if k.startswith(user_id)]
            for k in keys_to_remove:
                del self._usage_cache[k]
        else:
            self._usage_cache.clear()

    # ─── Summary ───────────────────────────────────────────────────

    async def get_license_summary(self, db, user_id: str) -> dict:
        """Get a complete license summary for a user."""
        license_obj = await db.query(License).filter(
            License.user_id == user_id,
        ).first()

        if not license_obj:
            return {
                "has_license": False,
                "plan": "free",
                "status": "no_license",
            }

        plan_id = license_obj.plan_id
        limits = self.get_plan_limits(plan_id)
        today_usage = self.get_usage(user_id)

        return {
            "has_license": True,
            "plan": plan_id,
            "status": license_obj.status,
            "is_trial": license_obj.is_trial,
            "issued_at": license_obj.issued_at.isoformat() if license_obj.issued_at else None,
            "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else None,
            "is_expired": license_obj.is_expired,
            "days_remaining": license_obj.days_remaining,
            "limits": limits,
            "today_usage": today_usage,
            "features": limits.get("features", []),
        }
