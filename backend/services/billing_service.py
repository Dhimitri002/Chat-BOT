"""
Flora Platform — Billing Service
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.models.subscription import Subscription, SubscriptionStatus
from backend.models.payment import Payment, PaymentStatus
from backend.models.bot import Bot, BotStatus
from backend.models.plan import Plan


class BillingService:
    """Service for managing subscriptions, payments, and billing operations."""

    @staticmethod
    async def create_subscription(
        db: AsyncSession,
        user_id: str,
        plan_id: str,
        billing_cycle: str = "monthly",
        payment_provider: str = "stripe",
    ) -> Subscription:
        """Create a new subscription for a user."""
        # Verify plan exists
        result = await db.execute(select(Plan).where(Plan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        now = datetime.now(timezone.utc)
        # Calculate period end based on billing cycle
        if billing_cycle == "yearly":
            period_end = now + timedelta(days=365)
            price = plan.price_yearly
        else:
            period_end = now + timedelta(days=30)
            price = plan.price_monthly

        subscription = Subscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            plan_id=plan_id,
            license_id=None,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=billing_cycle,
            price_paid=price,
            currency="BRL",
            started_at=now,
            expires_at=period_end,
            canceled_at=None,
            auto_renew=True,
            payment_method="",
            payment_provider=payment_provider,
            payment_provider_id="",
            last_payment_at=None,
            next_payment_at=period_end,
            grace_period_end=None,
            cancellation_reason="",
            created_at=now,
            updated_at=now,
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return subscription

    @staticmethod
    async def cancel_subscription(
        db: AsyncSession,
        subscription_id: str,
        reason: str = "",
    ) -> Subscription:
        """Cancel a subscription."""
        result = await db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        now = datetime.now(timezone.utc)
        subscription.status = SubscriptionStatus.CANCELED
        subscription.canceled_at = now
        subscription.cancellation_reason = reason
        subscription.auto_renew = False
        subscription.updated_at = now

        await db.commit()
        await db.refresh(subscription)
        return subscription

    @staticmethod
    async def renew_subscription(db: AsyncSession, subscription_id: str) -> Subscription:
        """Renew a subscription for another billing period."""
        result = await db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        # Get plan for pricing
        plan_result = await db.execute(
            select(Plan).where(Plan.id == subscription.plan_id)
        )
        plan = plan_result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        # Calculate new period
        if subscription.billing_cycle == "yearly":
            period_delta = timedelta(days=365)
            price = plan.price_yearly if plan else subscription.price_paid
        else:
            period_delta = timedelta(days=30)
            price = plan.price_monthly if plan else subscription.price_paid

        # Extend from current expiry or now, whichever is later
        base_date = subscription.expires_at if subscription.expires_at and subscription.expires_at > now else now

        subscription.expires_at = base_date + period_delta
        subscription.next_payment_at = subscription.expires_at
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.price_paid = price
        subscription.last_payment_at = now
        subscription.canceled_at = None
        subscription.cancellation_reason = ""
        subscription.updated_at = now

        await db.commit()
        await db.refresh(subscription)
        return subscription

    @staticmethod
    async def check_expiring_subscriptions(db: AsyncSession) -> list[Subscription]:
        """Find subscriptions expiring in the next 3 days."""
        now = datetime.now(timezone.utc)
        three_days_from_now = now + timedelta(days=3)

        result = await db.execute(
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .where(Subscription.expires_at <= three_days_from_now)
            .where(Subscription.expires_at > now)
            .order_by(Subscription.expires_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def check_expired_subscriptions(db: AsyncSession) -> list[Subscription]:
        """Find subscriptions that have just expired."""
        now = datetime.now(timezone.utc)

        result = await db.execute(
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .where(Subscription.expires_at <= now)
            .order_by(Subscription.expires_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def suspend_expired_bots(db: AsyncSession, subscription_id: str) -> dict:
        """Suspend all bots belonging to a user when their subscription expires."""
        # Get the subscription to find the user
        sub_result = await db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = sub_result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        # Find all active bots for this user
        bots_result = await db.execute(
            select(Bot)
            .where(Bot.user_id == subscription.user_id)
            .where(Bot.status == BotStatus.CONNECTED)
        )
        bots = bots_result.scalars().all()

        suspended_count = 0
        for bot in bots:
            bot.status = BotStatus.PAUSED
            bot.updated_at = datetime.now(timezone.utc)
            suspended_count += 1

        # Update subscription status
        subscription.status = SubscriptionStatus.EXPIRED
        subscription.updated_at = datetime.now(timezone.utc)

        await db.commit()
        return {
            "success": True,
            "suspended_bots": suspended_count,
            "subscription_id": subscription_id,
        }

    @staticmethod
    async def create_payment(
        db: AsyncSession,
        user_id: str,
        subscription_id: str,
        amount: float,
        provider: str,
        payment_method: str = "credit_card",
    ) -> Payment:
        """Create a payment record."""
        now = datetime.now(timezone.utc)
        payment = Payment(
            id=str(uuid.uuid4()),
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            currency="BRL",
            status=PaymentStatus.PENDING,
            provider=provider,
            provider_payment_id="",
            provider_charge_id="",
            payment_method=payment_method,
            description=f"Subscription payment via {provider}",
            metadata_json={},
            paid_at=None,
            refunded_at=None,
            refund_reason="",
            created_at=now,
            updated_at=now,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def confirm_payment(db: AsyncSession, payment_id: str) -> Payment:
        """Mark a payment as completed."""
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        now = datetime.now(timezone.utc)
        payment.status = PaymentStatus.COMPLETED
        payment.paid_at = now
        payment.updated_at = now

        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def get_user_payments(db: AsyncSession, user_id: str, limit: int = 20) -> list[Payment]:
        """Get payment history for a user."""
        result = await db.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
