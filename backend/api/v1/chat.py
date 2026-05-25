"""Flora Platform — Chat Endpoints"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.models.bot import Bot
from backend.models.message import Message
from backend.models.user import User
from backend.schemas.chat import SendMessageRequest, ChatHistoryResponse, ChatHistoryItem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all conversations for the current user's bots."""
    bots_result = await db.execute(select(Bot.id).where(Bot.owner_id == current_user.id))
    bot_ids = [row[0] for row in bots_result.all()]

    if not bot_ids:
        return {"conversations": [], "total": 0, "page": page, "page_size": page_size}

    conv_query = (
        select(
            Message.bot_id,
            Message.user_phone,
            func.max(Message.created_at).label("last_message_at"),
            func.count(Message.id).label("message_count"),
        )
        .where(Message.bot_id.in_(bot_ids))
        .group_by(Message.bot_id, Message.user_phone)
        .order_by(func.max(Message.created_at).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    conv_result = await db.execute(conv_query)
    conversations = conv_result.all()

    # Get bot names
    bot_names_result = await db.execute(select(Bot.id, Bot.name).where(Bot.id.in_(bot_ids)))
    bot_names = {str(r[0]): r[1] for r in bot_names_result.all()}

    # Get last messages for each conversation
    result = []
    for conv in conversations:
        last_msg_result = await db.execute(
            select(Message.content)
            .where(Message.bot_id == conv[0], Message.user_phone == conv[1])
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_msg = last_msg_result.scalar() or ""

        result.append({
            "bot_id": str(conv[0]),
            "bot_name": bot_names.get(str(conv[0]), "Bot"),
            "user_phone": conv[1],
            "last_message": last_msg[:100],
            "last_message_at": conv[2].isoformat(),
            "message_count": conv[3],
        })

    return {"conversations": result, "total": len(result), "page": page, "page_size": page_size}


@router.get("/history")
async def get_chat_history(
    bot_id: str = Query(...),
    user_phone: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for a specific conversation."""
    # Verify bot ownership
    bot_result = await db.execute(
        select(Bot).where(Bot.id == bot_id, Bot.owner_id == current_user.id)
    )
    if not bot_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    query = (
        select(Message)
        .where(Message.bot_id == bot_id, Message.user_phone == user_phone)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    # Count total
    count_result = await db.execute(
        select(func.count(Message.id)).where(
            Message.bot_id == bot_id, Message.user_phone == user_phone
        )
    )
    total = count_result.scalar()

    return {
        "items": [
            ChatHistoryItem(
                id=str(m.id),
                direction=m.direction,
                content=m.content,
                message_type=m.message_type,
                created_at=m.created_at,
            )
            for m in reversed(messages)  # Oldest first
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/send")
async def send_message(
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to a contact through a bot."""
    # Verify bot ownership
    bot_result = await db.execute(
        select(Bot).where(Bot.id == body.bot_id, Bot.owner_id == current_user.id)
    )
    bot = bot_result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    # Create message record
    msg = Message(
        id=str(uuid.uuid4()),
        bot_id=body.bot_id,
        user_phone=body.to,
        direction="outbound",
        content=body.content,
        message_type=body.message_type,
        status="sent",
    )
    db.add(msg)

    # Send via WhatsApp service
    from backend.services.whatsapp_service import whatsapp_service
    try:
        await whatsapp_service.send_message(bot_id=body.bot_id, to=body.to, message=body.content)
        await db.commit()
        return {"success": True, "message_id": msg.id}
    except Exception as e:
        msg.status = "failed"
        await db.commit()
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enviar mensagem")
