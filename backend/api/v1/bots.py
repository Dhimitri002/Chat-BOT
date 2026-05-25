"""Flora Platform — Bot Management Endpoints"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.models.bot import Bot, BotStatus
from backend.models.user import User
from backend.schemas.bot import BotCreateRequest, BotResponse, BotUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bots", tags=["bots"])


@router.get("")
async def list_bots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all bots owned by the current user."""
    query = select(Bot).where(Bot.owner_id == current_user.id)
    count_query = select(func.count(Bot.id)).where(Bot.owner_id == current_user.id)

    total = (await db.execute(count_query)).scalar()
    query = query.order_by(Bot.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    bots = result.scalars().all()

    return {
        "bots": [BotResponse.model_validate(b) for b in bots],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{bot_id}")
async def get_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific bot by ID."""
    result = await db.execute(
        select(Bot).where(Bot.id == bot_id, Bot.owner_id == current_user.id)
    )
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    return BotResponse.model_validate(bot)


@router.post("", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    body: BotCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new bot for the current user."""
    # Check license allows bot creation
    from backend.services.license_service import LicenseService
    license_check = await LicenseService().check_license_for_bot_creation(db, str(current_user.id))
    if not license_check["can_create"]:
        raise HTTPException(status_code=403, detail=license_check["reason"])

    bot = Bot(
        id=str(uuid.uuid4()),
        name=body.name,
        description=body.description or "",
        owner_id=str(current_user.id),
        status=BotStatus.DISCONNECTED,
        system_prompt=body.system_prompt or "",
        welcome_message=body.welcome_message or "Olá! 👋 Como posso te ajudar?",
        personality=body.personality or "friendly",
        language=body.language or "pt-BR",
        is_active=False,
    )
    db.add(bot)
    await db.commit()
    await db.refresh(bot)
    logger.info(f"Bot created: {bot.name} by user {current_user.id}")
    return BotResponse.model_validate(bot)


@router.put("/{bot_id}")
async def update_bot(
    bot_id: str,
    body: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a bot's configuration."""
    result = await db.execute(
        select(Bot).where(Bot.id == bot_id, Bot.owner_id == current_user.id)
    )
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(bot, field) and value is not None:
            setattr(bot, field, value)

    await db.commit()
    await db.refresh(bot)
    return BotResponse.model_validate(bot)


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a bot and all associated data."""
    result = await db.execute(
        select(Bot).where(Bot.id == bot_id, Bot.owner_id == current_user.id)
    )
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    await db.delete(bot)
    await db.commit()
    return {"success": True, "message": "Bot removido com sucesso"}


@router.post("/{bot_id}/activate")
async def activate_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate a bot (enable message processing)."""
    result = await db.execute(
        select(Bot).where(Bot.id == bot_id, Bot.owner_id == current_user.id)
    )
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    bot.is_active = True
    await db.commit()
    return {"success": True, "message": "Bot ativado"}


@router.post("/{bot_id}/deactivate")
async def deactivate_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a bot (pause message processing)."""
    result = await db.execute(
        select(Bot).where(Bot.id == bot_id, Bot.owner_id == current_user.id)
    )
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    bot.is_active = False
    await db.commit()
    return {"success": True, "message": "Bot desativado"}
