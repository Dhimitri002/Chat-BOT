"""
Flora Platform — Analytics Service
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bot import Bot, BotStatus
from backend.models.user import User
from backend.models.message import Message
from backend.models.intent import Intent
from backend.models.command import Command
from backend.models.license import License
from backend.models.subscription import Subscription, SubscriptionStatus
from backend.models.llm_usage import LLMUsage
from backend.models.payment import Payment, PaymentStatus


class AnalyticsService:
    """Service for generating analytics and statistics."""

    @staticmethod
    async def get_bot_stats(db: AsyncSession, bot_id: str, period_days: int = 30) -> dict:
        """Get comprehensive bot statistics for a given period."""
        since = datetime.now(timezone.utc) - timedelta(days=period_days)

        # Total messages
        total_messages = (await db.execute(
            select(func.count(Message.id))
            .where(Message.bot_id == bot_id)
            .where(Message.created_at >= since)
        )).scalar() or 0

        # Inbound messages
        inbound = (await db.execute(
            select(func.count(Message.id))
            .where(Message.bot_id == bot_id)
            .where(Message.direction == "inbound")
            .where(Message.created_at >= since)
        )).scalar() or 0

        # Outbound messages
        outbound = (await db.execute(
            select(func.count(Message.id))
            .where(Message.bot_id == bot_id)
            .where(Message.direction == "outbound")
            .where(Message.created_at >= since)
        )).scalar() or 0

        # Unique users
        unique_users = (await db.execute(
            select(func.count(func.distinct(Message.user_phone)))
            .where(Message.bot_id == bot_id)
            .where(Message.created_at >= since)
        )).scalar() or 0

        # Intents matched
        intents_matched = (await db.execute(
            select(func.count(Message.id))
            .where(Message.bot_id == bot_id)
            .where(Message.intent_matched != "")
            .where(Message.created_at >= since)
        )).scalar() or 0

        # Commands used
        commands_used = (await db.execute(
            select(func.count(Message.id))
            .where(Message.bot_id == bot_id)
            .where(Message.command_used != "")
            .where(Message.created_at >= since)
        )).scalar() or 0

        # LLM tokens
        llm_tokens = (await db.execute(
            select(func.sum(Message.llm_tokens_used))
            .where(Message.bot_id == bot_id)
            .where(Message.created_at >= since)
        )).scalar() or 0

        # LLM cost
        llm_cost = (await db.execute(
            select(func.sum(Message.llm_cost))
            .where(Message.bot_id == bot_id)
            .where(Message.created_at >= since)
        )).scalar() or 0.0

        # Messages per day
        messages_per_day = await AnalyticsService.get_messages_per_day(db, bot_id, period_days)

        # Top intents
        top_intents = await AnalyticsService.get_top_intents(db, bot_id, limit=10)

        # Top commands
        top_commands = await AnalyticsService.get_top_commands(db, bot_id, limit=10)

        return {
            "bot_id": bot_id,
            "period_days": period_days,
            "total_messages": total_messages,
            "inbound_messages": inbound,
            "outbound_messages": outbound,
            "unique_users": unique_users,
            "intents_matched": intents_matched,
            "commands_used": commands_used,
            "llm_tokens_used": llm_tokens or 0,
            "llm_cost": float(llm_cost or 0),
            "messages_per_day": messages_per_day,
            "top_intents": top_intents,
            "top_commands": top_commands,
        }

    @staticmethod
    async def get_admin_dashboard_stats(db: AsyncSession) -> dict:
        """Get admin dashboard statistics for the entire platform."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Total users
        total_users = (await db.execute(
            select(func.count(User.id))
        )).scalar() or 0

        # Active users (logged in within last 30 days)
        active_users = (await db.execute(
            select(func.count(User.id))
            .where(User.is_active == True)
        )).scalar() or 0

        # Total bots
        total_bots = (await db.execute(
            select(func.count(Bot.id))
        )).scalar() or 0

        # Active bots (connected)
        active_bots = (await db.execute(
            select(func.count(Bot.id))
            .where(Bot.status == BotStatus.CONNECTED)
        )).scalar() or 0

        # Total licenses
        total_licenses = (await db.execute(
            select(func.count(License.id))
        )).scalar() or 0

        # Active licenses
        active_licenses = (await db.execute(
            select(func.count(License.id))
            .where(License.status == "active")
        )).scalar() or 0

        # Expiring licenses (within 7 days)
        expiring_licenses = (await db.execute(
            select(func.count(License.id))
            .where(License.status == "active")
            .where(License.expires_at <= now + timedelta(days=7))
            .where(License.expires_at > now)
        )).scalar() or 0

        # Total revenue (completed payments)
        total_revenue = (await db.execute(
            select(func.sum(Payment.amount))
            .where(Payment.status == PaymentStatus.COMPLETED)
        )).scalar() or 0.0

        # Monthly revenue
        monthly_revenue = (await db.execute(
            select(func.sum(Payment.amount))
            .where(Payment.status == PaymentStatus.COMPLETED)
            .where(Payment.paid_at >= month_start)
        )).scalar() or 0.0

        # Messages today
        messages_today = (await db.execute(
            select(func.count(Message.id))
            .where(Message.created_at >= today_start)
        )).scalar() or 0

        # Messages this month
        messages_this_month = (await db.execute(
            select(func.count(Message.id))
            .where(Message.created_at >= month_start)
        )).scalar() or 0

        # LLM tokens today
        llm_tokens_today = (await db.execute(
            select(func.sum(LLMUsage.tokens_input + LLMUsage.tokens_output))
            .where(LLMUsage.created_at >= today_start)
        )).scalar() or 0

        # LLM cost today
        llm_cost_today = (await db.execute(
            select(func.sum(LLMUsage.cost))
            .where(LLMUsage.created_at >= today_start)
        )).scalar() or 0.0

        # New users today
        new_users_today = (await db.execute(
            select(func.count(User.id))
            .where(User.created_at >= today_start)
        )).scalar() or 0

        # New users this month
        new_users_this_month = (await db.execute(
            select(func.count(User.id))
            .where(User.created_at >= month_start)
        )).scalar() or 0

        # Revenue by month
        revenue_by_month = await AnalyticsService.get_revenue_by_month(db, months=12)

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_bots": total_bots,
            "active_bots": active_bots,
            "total_licenses": total_licenses,
            "active_licenses": active_licenses,
            "expiring_licenses": expiring_licenses,
            "total_revenue": float(total_revenue or 0),
            "monthly_revenue": float(monthly_revenue or 0),
            "messages_today": messages_today,
            "messages_this_month": messages_this_month,
            "llm_tokens_today": llm_tokens_today or 0,
            "llm_cost_today": float(llm_cost_today or 0),
            "new_users_today": new_users_today,
            "new_users_this_month": new_users_this_month,
            "revenue_by_month": revenue_by_month,
        }

    @staticmethod
    async def get_llm_usage_stats(
        db: AsyncSession,
        user_id: Optional[str] = None,
        bot_id: Optional[str] = None,
        period_days: int = 30,
    ) -> dict:
        """Get LLM usage statistics, optionally filtered by user or bot."""
        since = datetime.now(timezone.utc) - timedelta(days=period_days)

        query = select(LLMUsage).where(LLMUsage.created_at >= since)
        if user_id:
            query = query.where(LLMUsage.user_id == user_id)
        if bot_id:
            query = query.where(LLMUsage.bot_id == bot_id)

        # Total tokens input
        total_tokens_input = (await db.execute(
            select(func.sum(LLMUsage.tokens_input)).where(LLMUsage.created_at >= since)
        )).scalar() or 0

        # Total tokens output
        total_tokens_output = (await db.execute(
            select(func.sum(LLMUsage.tokens_output)).where(LLMUsage.created_at >= since)
        )).scalar() or 0

        # Total cost
        total_cost = (await db.execute(
            select(func.sum(LLMUsage.cost)).where(LLMUsage.created_at >= since)
        )).scalar() or 0.0

        # Total requests
        total_requests = (await db.execute(
            select(func.count(LLMUsage.id)).where(LLMUsage.created_at >= since)
        )).scalar() or 0

        # Success count
        success_count = (await db.execute(
            select(func.count(LLMUsage.id))
            .where(LLMUsage.created_at >= since)
            .where(LLMUsage.success == True)
        )).scalar() or 0

        # Average latency
        avg_latency = (await db.execute(
            select(func.avg(LLMUsage.latency_ms)).where(LLMUsage.created_at >= since)
        )).scalar() or 0.0

        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0.0

        # Usage by model
        model_result = await db.execute(
            select(
                LLMUsage.model,
                func.count(LLMUsage.id).label("requests"),
                func.sum(LLMUsage.tokens_input + LLMUsage.tokens_output).label("tokens"),
                func.sum(LLMUsage.cost).label("cost"),
            )
            .where(LLMUsage.created_at >= since)
            .group_by(LLMUsage.model)
        )
        usage_by_model = {}
        for row in model_result.all():
            usage_by_model[row.model] = {
                "requests": row.requests,
                "tokens": row.tokens or 0,
                "cost": float(row.cost or 0),
            }

        # Usage by day
        day_result = await db.execute(
            select(
                func.date(LLMUsage.created_at).label("day"),
                func.count(LLMUsage.id).label("requests"),
                func.sum(LLMUsage.tokens_input + LLMUsage.tokens_output).label("tokens"),
                func.sum(LLMUsage.cost).label("cost"),
            )
            .where(LLMUsage.created_at >= since)
            .group_by(func.date(LLMUsage.created_at))
            .order_by(func.date(LLMUsage.created_at))
        )
        usage_by_day = {}
        for row in day_result.all():
            day_str = str(row.day)
            usage_by_day[day_str] = {
                "requests": row.requests,
                "tokens": row.tokens or 0,
                "cost": float(row.cost or 0),
            }

        return {
            "total_tokens_input": total_tokens_input or 0,
            "total_tokens_output": total_tokens_output or 0,
            "total_cost": float(total_cost or 0),
            "total_requests": total_requests,
            "success_rate": round(success_rate, 2),
            "avg_latency_ms": round(float(avg_latency or 0), 2),
            "usage_by_model": usage_by_model,
            "usage_by_day": usage_by_day,
        }

    @staticmethod
    async def get_messages_per_day(
        db: AsyncSession,
        bot_id: str,
        period_days: int = 30,
    ) -> dict:
        """Get message counts grouped by day for a bot."""
        since = datetime.now(timezone.utc) - timedelta(days=period_days)

        result = await db.execute(
            select(
                func.date(Message.created_at).label("day"),
                func.count(Message.id).label("count"),
            )
            .where(Message.bot_id == bot_id)
            .where(Message.created_at >= since)
            .group_by(func.date(Message.created_at))
            .order_by(func.date(Message.created_at))
        )

        return {str(row.day): row.count for row in result.all()}

    @staticmethod
    async def get_top_intents(db: AsyncSession, bot_id: str, limit: int = 10) -> list[dict]:
        """Get the most matched intents for a bot."""
        result = await db.execute(
            select(
                Intent.name,
                Intent.match_count,
            )
            .where(Intent.bot_id == bot_id)
            .where(Intent.match_count > 0)
            .order_by(Intent.match_count.desc())
            .limit(limit)
        )

        return [
            {"name": row.name, "match_count": row.match_count}
            for row in result.all()
        ]

    @staticmethod
    async def get_top_commands(db: AsyncSession, bot_id: str, limit: int = 10) -> list[dict]:
        """Get the most used commands for a bot."""
        result = await db.execute(
            select(
                Command.name,
                Command.use_count,
            )
            .where(Command.bot_id == bot_id)
            .where(Command.use_count > 0)
            .order_by(Command.use_count.desc())
            .limit(limit)
        )

        return [
            {"name": row.name, "use_count": row.use_count}
            for row in result.all()
        ]

    @staticmethod
    async def get_revenue_by_month(db: AsyncSession, months: int = 12) -> dict:
        """Get revenue grouped by month."""
        since = datetime.now(timezone.utc) - timedelta(days=months * 30)

        result = await db.execute(
            select(
                func.strftime("%Y-%m", Payment.paid_at).label("month"),
                func.sum(Payment.amount).label("revenue"),
            )
            .where(Payment.status == PaymentStatus.COMPLETED)
            .where(Payment.paid_at >= since)
            .group_by(func.strftime("%Y-%m", Payment.paid_at))
            .order_by(func.strftime("%Y-%m", Payment.paid_at))
        )

        return {row.month: float(row.revenue or 0) for row in result.all() if row.month}
