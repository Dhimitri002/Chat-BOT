"""
Flora Platform — Bot Service
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.models.bot import Bot, BotStatus
from backend.models.intent import Intent
from backend.models.command import Command
from backend.models.message import Message
from backend.models.whatsapp_session import WhatsAppSession
from backend.schemas.bot import BotCreate, BotUpdate


class BotService:
    """Service for managing bots and their associated resources."""

    @staticmethod
    async def get_bot(db: AsyncSession, bot_id: str, user_id: Optional[str] = None) -> Bot:
        """Get a bot by its ID, optionally filtering by user_id for ownership check."""
        query = select(Bot).where(Bot.id == bot_id)
        if user_id is not None:
            query = query.where(Bot.user_id == user_id)

        result = await db.execute(query)
        bot = result.scalar_one_or_none()

        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found",
            )
        return bot

    @staticmethod
    async def get_bots(db: AsyncSession, user_id: str, skip: int = 0, limit: int = 20) -> list[Bot]:
        """List all bots belonging to a user with pagination."""
        result = await db.execute(
            select(Bot)
            .where(Bot.user_id == user_id)
            .order_by(Bot.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_bot(db: AsyncSession, data: dict, user_id: str) -> Bot:
        """Create a new bot for the given user."""
        now = datetime.now(timezone.utc)
        bot = Bot(
            id=str(uuid.uuid4()),
            name=data.get("name", "Novo Bot"),
            user_id=user_id,
            status=BotStatus.DISCONNECTED,
            config=data.get("config", {}),
            system_prompt=data.get("system_prompt", ""),
            command_prefix=data.get("command_prefix", "/"),
            llm_model=data.get("llm_model", ""),
            llm_provider=data.get("llm_provider", ""),
            llm_temperature=data.get("llm_temperature", 0.7),
            llm_max_tokens=data.get("llm_max_tokens", 500),
            welcome_message=data.get("welcome_message", "Olá! Como posso te ajudar?"),
            goodbye_message=data.get("goodbye_message", "Até mais!"),
            error_message=data.get("error_message", "Desculpe, ocorreu um erro. Tente novamente."),
            created_at=now,
            updated_at=now,
        )
        db.add(bot)
        await db.commit()
        await db.refresh(bot)
        return bot

    @staticmethod
    async def update_bot(db: AsyncSession, bot_id: str, data: dict, user_id: str) -> Bot:
        """Update fields of an existing bot. Only provided fields are updated."""
        bot = await BotService.get_bot(db, bot_id, user_id)

        updatable_fields = {
            "name", "config", "system_prompt", "command_prefix",
            "llm_model", "llm_provider", "llm_temperature", "llm_max_tokens",
            "welcome_message", "goodbye_message", "error_message", "status",
        }

        for field, value in data.items():
            if field in updatable_fields and value is not None:
                setattr(bot, field, value)

        bot.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(bot)
        return bot

    @staticmethod
    async def delete_bot(db: AsyncSession, bot_id: str, user_id: str) -> dict:
        """Delete a bot and all its cascading resources."""
        bot = await BotService.get_bot(db, bot_id, user_id)

        # Delete associated intents
        await db.execute(
            delete(Intent).where(Intent.bot_id == bot_id)
        )
        # Delete associated commands
        await db.execute(
            delete(Command).where(Command.bot_id == bot_id)
        )

        await db.delete(bot)
        await db.commit()
        return {"success": True, "message": f"Bot {bot_id} deleted successfully"}

    @staticmethod
    async def get_bot_stats(db: AsyncSession, bot_id: str, period_days: int = 30) -> dict:
        """Get comprehensive statistics for a bot over a given period."""
        bot = await BotService.get_bot(db, bot_id)

        since = datetime.now(timezone.utc) - timedelta(days=period_days)

        # Total messages in period
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

        # LLM tokens used
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

        # Total intents configured
        total_intents = (await db.execute(
            select(func.count(Intent.id))
            .where(Intent.bot_id == bot_id)
        )).scalar() or 0

        # Total commands configured
        total_commands = (await db.execute(
            select(func.count(Command.id))
            .where(Command.bot_id == bot_id)
        )).scalar() or 0

        return {
            "bot_id": bot_id,
            "period_days": period_days,
            "total_messages": total_messages,
            "inbound_messages": inbound,
            "outbound_messages": outbound,
            "unique_users": unique_users,
            "intents_matched": intents_matched,
            "commands_used": commands_used,
            "llm_tokens_used": llm_tokens,
            "llm_cost": float(llm_cost),
            "total_intents": total_intents,
            "total_commands": total_commands,
            "bot_status": bot.status,
        }

    @staticmethod
    async def add_intent(db: AsyncSession, bot_id: str, intent_data: dict) -> Intent:
        """Add a new intent to a bot."""
        # Verify bot exists
        await BotService.get_bot(db, bot_id)

        now = datetime.now(timezone.utc)
        intent = Intent(
            id=str(uuid.uuid4()),
            bot_id=bot_id,
            name=intent_data.get("name", "Novo Intent"),
            description=intent_data.get("description", ""),
            keywords=intent_data.get("keywords", []),
            responses=intent_data.get("responses", []),
            priority=intent_data.get("priority", 0),
            is_active=intent_data.get("is_active", True),
            match_count=0,
            created_at=now,
            updated_at=now,
        )
        db.add(intent)
        await db.commit()
        await db.refresh(intent)
        return intent

    @staticmethod
    async def remove_intent(db: AsyncSession, bot_id: str, intent_id: str) -> dict:
        """Remove an intent from a bot."""
        result = await db.execute(
            select(Intent).where(Intent.id == intent_id).where(Intent.bot_id == bot_id)
        )
        intent = result.scalar_one_or_none()

        if not intent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intent not found",
            )

        await db.delete(intent)
        await db.commit()
        return {"success": True, "message": f"Intent {intent_id} removed successfully"}

    @staticmethod
    async def add_command(db: AsyncSession, bot_id: str, command_data: dict) -> Command:
        """Add a new command to a bot."""
        # Verify bot exists
        await BotService.get_bot(db, bot_id)

        now = datetime.now(timezone.utc)
        command = Command(
            id=str(uuid.uuid4()),
            bot_id=bot_id,
            name=command_data.get("name", "Novo Comando"),
            description=command_data.get("description", ""),
            trigger=command_data.get("trigger", ""),
            response=command_data.get("response", ""),
            response_type=command_data.get("response_type", "text"),
            is_active=command_data.get("is_active", True),
            use_count=0,
            version=1,
            created_at=now,
            updated_at=now,
        )
        db.add(command)
        await db.commit()
        await db.refresh(command)
        return command

    @staticmethod
    async def remove_command(db: AsyncSession, bot_id: str, command_id: str) -> dict:
        """Remove a command from a bot."""
        result = await db.execute(
            select(Command).where(Command.id == command_id).where(Command.bot_id == bot_id)
        )
        command = result.scalar_one_or_none()

        if not command:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Command not found",
            )

        await db.delete(command)
        await db.commit()
        return {"success": True, "message": f"Command {command_id} removed successfully"}
