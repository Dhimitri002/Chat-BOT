"""
Flora Platform — Chat Service
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.models.message import Message
from backend.models.bot import Bot, BotStatus
from backend.models.intent import Intent
from backend.models.command import Command


class ChatService:
    """Service for processing and managing chat messages."""

    @staticmethod
    async def process_incoming_message(
        db: AsyncSession,
        bot_id: str,
        user_phone: str,
        content: str,
        message_type: str = "text",
    ) -> dict:
        """
        Process an incoming message through the pipeline:
        1. Save the inbound message
        2. Try to match an intent
        3. Try to match a command
        4. Fallback response if nothing matches
        """
        # Verify bot exists and is active
        result = await db.execute(select(Bot).where(Bot.id == bot_id))
        bot = result.scalar_one_or_none()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found",
            )

        if bot.status != BotStatus.CONNECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is not connected",
            )

        # Step 1: Save inbound message
        inbound_msg = await ChatService.save_message(
            db, bot_id, user_phone, "inbound", content, message_type
        )

        # Step 2: Try to match a command first (commands take priority)
        command_response = await ChatService._try_match_command(db, bot, content)
        if command_response:
            outbound_msg = await ChatService.save_message(
                db, bot_id, user_phone, "outbound",
                command_response["response"], "text",
                command_used=command_response["command_name"],
            )
            return {
                "reply": command_response["response"],
                "source": "command",
                "command": command_response["command_name"],
                "message_id": outbound_msg.id,
            }

        # Step 3: Try to match an intent
        intent_response = await ChatService._try_match_intent(db, bot_id, content)
        if intent_response:
            outbound_msg = await ChatService.save_message(
                db, bot_id, user_phone, "outbound",
                intent_response["response"], "text",
                intent_matched=intent_response["intent_name"],
            )
            return {
                "reply": intent_response["response"],
                "source": "intent",
                "intent": intent_response["intent_name"],
                "message_id": outbound_msg.id,
            }

        # Step 4: Fallback
        fallback_msg = bot.error_message or "Desculpe, não entendi. Pode reformular?"
        outbound_msg = await ChatService.save_message(
            db, bot_id, user_phone, "outbound", fallback_msg, "text"
        )
        return {
            "reply": fallback_msg,
            "source": "fallback",
            "message_id": outbound_msg.id,
        }

    @staticmethod
    async def _try_match_command(db: AsyncSession, bot: Bot, content: str) -> Optional[dict]:
        """Try to match a command based on the bot's command prefix and triggers."""
        prefix = bot.command_prefix or "/"
        if not content.startswith(prefix):
            return None

        # Extract the command trigger (first word without prefix)
        parts = content[len(prefix):].strip().split()
        if not parts:
            return None
        trigger = parts[0].lower()

        # Find matching active command
        result = await db.execute(
            select(Command)
            .where(Command.bot_id == bot.id)
            .where(Command.is_active == True)
        )
        commands = result.scalars().all()

        for cmd in commands:
            if cmd.trigger.lower() == trigger:
                # Increment use count
                cmd.use_count += 1
                await db.commit()
                return {
                    "command_name": cmd.name,
                    "response": cmd.response or f"Comando {cmd.name} executado.",
                }
        return None

    @staticmethod
    async def _try_match_intent(db: AsyncSession, bot_id: str, content: str) -> Optional[dict]:
        """Try to match an intent based on keywords."""
        content_lower = content.lower()

        result = await db.execute(
            select(Intent)
            .where(Intent.bot_id == bot_id)
            .where(Intent.is_active == True)
            .order_by(Intent.priority.desc())
        )
        intents = result.scalars().all()

        for intent in intents:
            keywords = intent.keywords or []
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    # Increment match count
                    intent.match_count += 1
                    await db.commit()

                    responses = intent.responses or []
                    if responses:
                        import random
                        response = random.choice(responses)
                    else:
                        response = ""

                    return {
                        "intent_name": intent.name,
                        "response": response,
                    }
        return None

    @staticmethod
    async def save_message(
        db: AsyncSession,
        bot_id: str,
        user_phone: str,
        direction: str,
        content: str,
        message_type: str = "text",
        **kwargs,
    ) -> Message:
        """Save a message to the database."""
        now = datetime.now(timezone.utc)
        message = Message(
            id=str(uuid.uuid4()),
            bot_id=bot_id,
            user_phone=user_phone,
            direction=direction,
            content=content,
            message_type=message_type,
            media_url=kwargs.get("media_url", ""),
            intent_matched=kwargs.get("intent_matched", ""),
            command_used=kwargs.get("command_used", ""),
            llm_model_used=kwargs.get("llm_model_used", ""),
            llm_tokens_used=kwargs.get("llm_tokens_used", 0),
            llm_cost=kwargs.get("llm_cost", 0.0),
            is_read=direction == "outbound",
            whatsapp_message_id=kwargs.get("whatsapp_message_id", ""),
            created_at=now,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_chat_history(
        db: AsyncSession,
        bot_id: str,
        user_phone: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """Get chat history for a bot, optionally filtered by user phone."""
        query = (
            select(Message)
            .where(Message.bot_id == bot_id)
            .order_by(Message.created_at.desc())
        )

        if user_phone:
            query = query.where(Message.user_phone == user_phone)

        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_conversations(
        db: AsyncSession,
        bot_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """Get a list of conversations (unique users) for a bot with last message info."""
        # Get distinct user_phones with their latest message
        subquery = (
            select(
                Message.user_phone,
                func.max(Message.created_at).label("last_message_at"),
                func.count(Message.id).label("message_count"),
            )
            .where(Message.bot_id == bot_id)
            .group_by(Message.user_phone)
            .order_by(func.max(Message.created_at).desc())
            .offset(offset)
            .limit(limit)
            .subquery()
        )

        result = await db.execute(
            select(
                subquery.c.user_phone,
                subquery.c.last_message_at,
                subquery.c.message_count,
            )
        )
        rows = result.all()

        conversations = []
        for row in rows:
            # Get the last message content for each conversation
            last_msg_result = await db.execute(
                select(Message.content)
                .where(Message.bot_id == bot_id)
                .where(Message.user_phone == row.user_phone)
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            last_content = last_msg_result.scalar() or ""

            # Get unread count
            unread_result = await db.execute(
                select(func.count(Message.id))
                .where(Message.bot_id == bot_id)
                .where(Message.user_phone == row.user_phone)
                .where(Message.is_read == False)
            )
            unread_count = unread_result.scalar() or 0

            conversations.append({
                "user_phone": row.user_phone,
                "last_message": last_content[:100],
                "last_message_at": row.last_message_at,
                "message_count": row.message_count,
                "unread_count": unread_count,
            })

        return conversations

    @staticmethod
    async def get_unread_count(
        db: AsyncSession,
        bot_id: str,
        user_phone: Optional[str] = None,
    ) -> int:
        """Get the count of unread messages for a bot, optionally filtered by user phone."""
        query = (
            select(func.count(Message.id))
            .where(Message.bot_id == bot_id)
            .where(Message.is_read == False)
        )

        if user_phone:
            query = query.where(Message.user_phone == user_phone)

        result = await db.execute(query)
        return result.scalar() or 0

    @staticmethod
    async def mark_as_read(db: AsyncSession, bot_id: str, user_phone: str) -> dict:
        """Mark all messages from a user as read."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Message)
            .where(Message.bot_id == bot_id)
            .where(Message.user_phone == user_phone)
            .where(Message.is_read == False)
        )
        unread_messages = result.scalars().all()

        count = 0
        for msg in unread_messages:
            msg.is_read = True
            count += 1

        await db.commit()
        return {"success": True, "marked_as_read": count}
