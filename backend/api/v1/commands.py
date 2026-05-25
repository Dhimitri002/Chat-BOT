"""Flora Platform — Command Management Endpoints"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.models.bot import Bot
from backend.models.command import Command
from backend.models.user import User
from backend.schemas.command import CommandCreate, CommandResponse, CommandUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/commands", tags=["commands"])


@router.get("")
async def list_commands(
    bot_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all commands for a specific bot."""
    bot_result = await db.execute(
        select(Bot).where(Bot.id == bot_id, Bot.owner_id == current_user.id)
    )
    bot = bot_result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    query = select(Command).where(Command.bot_id == bot_id)
    count_query = select(func.count(Command.id)).where(Command.bot_id == bot_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Command.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    commands = result.scalars().all()

    return {
        "commands": [CommandResponse.model_validate(c) for c in commands],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
async def create_command(
    body: CommandCreate,
    bot_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new command for a bot."""
    bot_result = await db.execute(
        select(Bot).where(Bot.id == bot_id, Bot.owner_id == current_user.id)
    )
    if not bot_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    cmd = Command(
        id=str(uuid.uuid4()),
        bot_id=bot_id,
        name=body.name,
        description=body.description,
        trigger=body.trigger,
        response=body.response,
        response_type=body.response_type,
        is_active=True,
    )
    db.add(cmd)
    await db.commit()
    await db.refresh(cmd)
    return CommandResponse.model_validate(cmd)


@router.put("/{command_id}")
async def update_command(
    command_id: str,
    body: CommandUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a command."""
    cmd_result = await db.execute(
        select(Command).join(Bot, Command.bot_id == Bot.id).where(
            Command.id == command_id, Bot.owner_id == current_user.id
        )
    )
    cmd = cmd_result.scalar_one_or_none()
    if not cmd:
        raise HTTPException(status_code=404, detail="Comando não encontrado")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(cmd, field) and value is not None:
            setattr(cmd, field, value)

    await db.commit()
    await db.refresh(cmd)
    return CommandResponse.model_validate(cmd)


@router.delete("/{command_id}")
async def delete_command(
    command_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a command."""
    cmd_result = await db.execute(
        select(Command).join(Bot, Command.bot_id == Bot.id).where(
            Command.id == command_id, Bot.owner_id == current_user.id
        )
    )
    cmd = cmd_result.scalar_one_or_none()
    if not cmd:
        raise HTTPException(status_code=404, detail="Comando não encontrado")

    await db.delete(cmd)
    await db.commit()
    return {"success": True, "message": "Comando removido"}


@router.post("/test")
async def test_command(
    body: dict,
    bot_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test a command trigger against a message."""
    message = body.get("message", "")
    prefix = body.get("prefix", "/")

    # Get bot's commands
    bot_result = await db.execute(
        select(Bot).where(Bot.id == bot_id, Bot.owner_id == current_user.id)
    )
    if not bot_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    cmd_result = await db.execute(
        select(Command).where(Command.bot_id == bot_id, Command.is_active == True)
    )
    commands = cmd_result.scalars().all()

    for cmd in commands:
        trigger = cmd.trigger
        if not trigger.startswith(prefix):
            trigger = prefix + trigger
        if message.strip().lower().startswith(trigger.lower()):
            return {
                "matched": True,
                "command_name": cmd.name,
                "trigger": cmd.trigger,
                "response": cmd.response,
            }

    return {"matched": False}
