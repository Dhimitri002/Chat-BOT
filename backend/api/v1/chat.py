"""Chat Endpoints — API para gerenciamento de conversas."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.core.chat_engine import ChatEngine
from backend.models.bot import Bot
from backend.models.message import Message
from backend.models.user import User
from backend.services.bot_service import BotService

router = APIRouter()


class SendMessageRequest(BaseModel):
    bot_id: str
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None


class ChatHistoryRequest(BaseModel):
    bot_id: str
    session_id: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)


@router.post("/send")
async def send_chat_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Envia mensagem para um bot e retorna a resposta."""
    bot = await BotService.get_bot(db, request.bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    if not bot.is_active:
        raise HTTPException(status_code=400, detail="Bot está inativo")

    chat_engine = ChatEngine(db, bot)
    result = await chat_engine.process_message(request.message, request.session_id)

    return {
        "message_id": result.get("session_id"),
        "content": result["content"],
        "type": result["type"],
        "session_id": result["session_id"],
        "metadata": result.get("metadata", {}),
    }


@router.get("/history/{bot_id}")
async def get_chat_history(
    bot_id: str,
    session_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém histórico de chat de um bot."""
    bot = await BotService.get_bot(db, bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    query = select(Message).where(Message.bot_id == bot_id)
    if session_id:
        query = query.where(Message.session_id == session_id)

    query = query.order_by(Message.created_at.desc()).limit(limit)
    result = await db.execute(query)
    messages = result.scalars().all()

    return {
        "messages": [
            {
                "id": str(m.id),
                "content": m.content,
                "direction": m.direction,
                "message_type": m.message_type,
                "metadata": m.metadata,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in reversed(messages)
        ],
        "total": len(messages),
    }


@router.post("/reset/{bot_id}")
async def reset_chat_session(
    bot_id: str,
    session_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reseta uma sessão de chat."""
    bot = await BotService.get_bot(db, bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    # Deletar mensagens da sessão
    await db.execute(
        Message.__table__.delete().where(
            Message.bot_id == bot_id,
            Message.session_id == session_id,
        )
    )
    await db.commit()

    return {"message": "Sessão resetada com sucesso"}


@router.get("/sessions")
async def list_chat_sessions(
    bot_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista sessões de chat ativas de um bot."""
    bot = await BotService.get_bot(db, bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    from sqlalchemy import func, distinct

    result = await db.execute(
        select(
            Message.session_id,
            func.count(Message.id).label("message_count"),
            func.max(Message.created_at).label("last_message_at"),
        )
        .where(Message.bot_id == bot_id)
        .group_by(Message.session_id)
        .order_by(func.max(Message.created_at).desc())
        .limit(50)
    )
    sessions = result.all()

    return {
        "sessions": [
            {
                "session_id": s[0],
                "message_count": s[1],
                "last_message_at": s[2].isoformat() if s[2] else None,
            }
            for s in sessions
        ],
        "total": len(sessions),
    }
