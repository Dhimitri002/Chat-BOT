"""Bot Service - Serviço de gerenciamento de bots com CRUD completo."""
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bot import Bot
from backend.models.message import Message
from backend.schemas.bot import BotCreateRequest, BotUpdateRequest


class BotService:
    """Serviço de gerenciamento de bots."""

    @staticmethod
    async def create_bot(db: AsyncSession, user_id: str, data: BotCreateRequest) -> Bot:
        """Cria um novo bot."""
        bot = Bot(
            id=str(uuid4()),
            owner_id=user_id,
            name=data.name,
            description=data.description or "",
            personality=data.personality or "amigável e prestativa",
            welcome_message=data.welcome_message or f"Olá! Sou {data.name}, como posso ajudar?",
            farewell_message=data.farewell_message or "Até logo! Foi um prazer ajudar.",
            is_active=True,
            config=data.config if hasattr(data, 'config') else {},
        )
        db.add(bot)
        await db.commit()
        await db.refresh(bot)
        return bot

    @staticmethod
    async def get_bot(db: AsyncSession, bot_id: str, user_id: Optional[str] = None) -> Optional[Bot]:
        """Busca bot por ID. Se user_id fornecido, verifica propriedade."""
        query = select(Bot).where(Bot.id == bot_id)
        if user_id:
            query = query.where(Bot.owner_id == user_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_bots(
        db: AsyncSession, user_id: str, page: int = 1, per_page: int = 20
    ) -> dict:
        """Lista bots do usuário com paginação."""
        # Count total
        count_result = await db.execute(
            select(func.count()).where(Bot.owner_id == user_id)
        )
        total = count_result.scalar() or 0

        # Fetch page
        offset = (page - 1) * per_page
        result = await db.execute(
            select(Bot)
            .where(Bot.owner_id == user_id)
            .order_by(Bot.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        bots = result.scalars().all()

        return {
            "items": bots,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": max(1, (total + per_page - 1) // per_page),
        }

    @staticmethod
    async def update_bot(
        db: AsyncSession, bot_id: str, user_id: str, data: BotUpdateRequest
    ) -> Optional[Bot]:
        """Atualiza um bot existente."""
        bot = await BotService.get_bot(db, bot_id, user_id)
        if not bot:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bot, field, value)

        await db.commit()
        await db.refresh(bot)
        return bot

    @staticmethod
    async def delete_bot(db: AsyncSession, bot_id: str, user_id: str) -> bool:
        """Deleta um bot e seus dados relacionados."""
        bot = await BotService.get_bot(db, bot_id, user_id)
        if not bot:
            return False

        # Deletar mensagens relacionadas
        await db.execute(
            Message.__table__.delete().where(Message.bot_id == bot_id)
        )

        # Deletar bot
        await db.delete(bot)
        await db.commit()
        return True

    @staticmethod
    async def clone_bot(
        db: AsyncSession, bot_id: str, user_id: str, new_name: str
    ) -> Optional[Bot]:
        """Clona um bot existente."""
        original = await BotService.get_bot(db, bot_id, user_id)
        if not original:
            return None

        cloned = Bot(
            id=str(uuid4()),
            owner_id=user_id,
            name=new_name,
            description=f"Cópia de {original.name}",
            personality=original.personality,
            welcome_message=original.welcome_message,
            farewell_message=original.farewell_message,
            is_active=True,
            config=original.config,
        )
        db.add(cloned)
        await db.commit()
        await db.refresh(cloned)
        return cloned

    @staticmethod
    async def get_bot_stats(db: AsyncSession, bot_id: str) -> dict:
        """Retorna estatísticas do bot."""
        # Total de mensagens
        msg_count_result = await db.execute(
            select(func.count()).where(Message.bot_id == bot_id)
        )
        total_messages = msg_count_result.scalar() or 0

        # Usuários únicos (sessões únicas)
        unique_users_result = await db.execute(
            select(func.count(func.distinct(Message.session_id)))
            .where(Message.bot_id == bot_id)
        )
        unique_users = unique_users_result.scalar() or 0

        # Mensagens nas últimas 24h
        from datetime import datetime, timedelta, timezone
        day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        recent_result = await db.execute(
            select(func.count())
            .where(Message.bot_id == bot_id)
            .where(Message.created_at >= day_ago)
        )
        messages_today = recent_result.scalar() or 0

        return {
            "total_messages": total_messages,
            "unique_users": unique_users,
            "messages_today": messages_today,
        }

    @staticmethod
    async def toggle_bot_active(db: AsyncSession, bot_id: str, user_id: str) -> Optional[Bot]:
        """Alterna status ativo/inativo do bot."""
        bot = await BotService.get_bot(db, bot_id, user_id)
        if not bot:
            return None

        bot.is_active = not bot.is_active
        await db.commit()
        await db.refresh(bot)
        return bot
