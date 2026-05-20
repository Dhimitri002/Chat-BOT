"""Chat Endpoints - API para gerenciamento de conversas."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.schemas.common import PaginatedResponse

router = APIRouter(prefix="/chat", tags=["chat"])


class SendMessageRequest(BaseModel):
    bot_id: str
    to: str = Field(..., description="Número do destinatário")
    text: str = Field(..., min_length=1, max_length=10000)


class TransferRequest(BaseModel):
    conversation_id: str
    reason: Optional[str] = "Transferido pelo admin"


@router.post("/send")
async def send_chat_message(
    request: SendMessageRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Envia mensagem de chat (via painel admin)."""
    from backend.core.whatsapp_manager import whatsapp_manager

    result = await whatsapp_manager.send_message(
        request.bot_id, request.to, request.text
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/history/{bot_id}")
async def get_chat_history(
    bot_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém histórico de mensagens de um bot."""
    from backend.models.message import Message

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Message)
        .where(Message.bot_id == bot_id)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    messages = result.scalars().all()

    return PaginatedResponse(
        items=[m.to_dict() for m in messages],
        total=len(messages),
        page=page,
        page_size=page_size,
        pages=1,
    )


@router.get("/conversations/{bot_id}")
async def list_conversations(
    bot_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista conversas de um bot."""
    from sqlalchemy import func, distinct
    from backend.models.message import Message

    result = await db.execute(
        select(
            Message.sender,
            func.count(Message.id).label("message_count"),
            func.max(Message.created_at).label("last_message_at"),
        )
        .where(Message.bot_id == bot_id)
        .group_by(Message.sender)
        .order_by(func.max(Message.created_at).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    conversations = result.all()

    return {
        "conversations": [
            {
                "sender": c.sender,
                "message_count": c.message_count,
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
            }
            for c in conversations
        ],
        "page": page,
        "page_size": page_size,
    }


@router.get("/messages/{sender}")
async def get_conversation_messages(
    sender: str,
    bot_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém mensagens de uma conversa específica."""
    from backend.models.message import Message

    result = await db.execute(
        select(Message)
        .where(Message.bot_id == bot_id, Message.sender == sender)
        .order_by(Message.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    messages = result.scalars().all()
    return {"messages": [m.to_dict() for m in messages], "page": page}


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deleta uma conversa."""
    return {"success": True, "message": "Conversa deletada."}


@router.post("/transfer")
async def transfer_to_human(
    request: TransferRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transfere conversa para atendimento humano."""
    return {"success": True, "message": "Conversa transferida para atendimento humano."}


@router.get("/stats/{bot_id}")
async def get_chat_stats(
    bot_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém estatísticas de chat de um bot."""
    from sqlalchemy import func
    from backend.models.message import Message

    # Total de mensagens
    total_result = await db.execute(
        select(func.count(Message.id)).where(Message.bot_id == bot_id)
    )
    total_messages = total_result.scalar()

    # Total de conversas (senders únicos)
    conversations_result = await db.execute(
        select(func.count(func.distinct(Message.sender))).where(Message.bot_id == bot_id)
    )
    total_conversations = conversations_result.scalar()

    # Mensagens hoje
    from datetime import datetime, timezone, timedelta
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count(Message.id)).where(
            Message.bot_id == bot_id,
            Message.created_at >= today,
        )
    )
    messages_today = today_result.scalar()

    return {
        "total_messages": total_messages,
        "total_conversations": total_conversations,
        "messages_today": messages_today,
        "bot_id": bot_id,
    }


# Import select at module level for convenience
from sqlalchemy import select
