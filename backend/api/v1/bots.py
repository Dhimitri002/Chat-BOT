"""Bot Endpoints — CRUD de bots com persistência real."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.core.chat_engine import ChatEngine
from backend.models.bot import Bot
from backend.models.user import User
from backend.schemas.bot import BotCreate, BotUpdate, BotResponse
from backend.services.bot_service import BotService

router = APIRouter()


class WhatsAppWebhook(BaseModel):
    """Payload do webhook WhatsApp."""
    text: str
    contact_id: str
    contact_name: str = "Usuario"
    bot_id: str = ""
    timestamp: str = ""


# ─── CRUD de Bots ─────────────────────────────────────────

@router.get("/", response_model=dict)
async def list_bots(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista bots do usuário autenticado."""
    result = await BotService.list_bots(db, str(current_user.id), page, per_page)
    return result


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_bot(
    data: BotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo bot."""
    bot = await BotService.create_bot(db, str(current_user.id), data)
    return {
        "id": str(bot.id),
        "name": bot.name,
        "description": bot.description,
        "personality": bot.personality,
        "welcome_message": bot.welcome_message,
        "is_active": bot.is_active,
        "created_at": bot.created_at.isoformat() if bot.created_at else None,
    }


@router.get("/{bot_id}", response_model=dict)
async def get_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém detalhes de um bot."""
    bot = await BotService.get_bot(db, bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    return {
        "id": str(bot.id),
        "name": bot.name,
        "description": bot.description,
        "personality": bot.personality,
        "welcome_message": bot.welcome_message,
        "farewell_message": bot.farewell_message,
        "is_active": bot.is_active,
        "config": bot.config,
        "created_at": bot.created_at.isoformat() if bot.created_at else None,
        "updated_at": bot.updated_at.isoformat() if bot.updated_at else None,
    }


@router.put("/{bot_id}", response_model=dict)
async def update_bot(
    bot_id: str,
    data: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza um bot existente."""
    bot = await BotService.update_bot(db, bot_id, str(current_user.id), data)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    return {
        "id": str(bot.id),
        "name": bot.name,
        "description": bot.description,
        "personality": bot.personality,
        "welcome_message": bot.welcome_message,
        "is_active": bot.is_active,
        "updated_at": bot.updated_at.isoformat() if bot.updated_at else None,
    }


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deleta um bot."""
    success = await BotService.delete_bot(db, bot_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    return None


@router.post("/{bot_id}/clone", response_model=dict)
async def clone_bot(
    bot_id: str,
    new_name: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clona um bot existente."""
    bot = await BotService.clone_bot(db, bot_id, str(current_user.id), new_name)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot original não encontrado")

    return {
        "id": str(bot.id),
        "name": bot.name,
        "message": "Bot clonado com sucesso",
    }


@router.get("/{bot_id}/stats", response_model=dict)
async def get_bot_stats(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém estatísticas de um bot."""
    bot = await BotService.get_bot(db, bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    stats = await BotService.get_bot_stats(db, bot_id)
    return stats


@router.post("/{bot_id}/toggle", response_model=dict)
async def toggle_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Alterna status ativo/inativo do bot."""
    bot = await BotService.toggle_bot_active(db, bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    return {
        "id": str(bot.id),
        "is_active": bot.is_active,
        "message": f"Bot {'ativado' if bot.is_active else 'desativado'}",
    }


# ─── Teste de Bot ─────────────────────────────────────────

@router.post("/{bot_id}/test", response_model=dict)
async def test_bot(
    bot_id: str,
    message: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Envia mensagem de teste para um bot."""
    bot = await BotService.get_bot(db, bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    if not bot.is_active:
        raise HTTPException(status_code=400, detail="Bot está inativo")

    chat_engine = ChatEngine(db, bot)
    result = await chat_engine.process_message(message)

    return {
        "bot_id": bot_id,
        "input": message,
        "output": result["content"],
        "type": result["type"],
        "session_id": result["session_id"],
    }


# ─── Webhook WhatsApp ─────────────────────────────────────

@router.post("/webhook/whatsapp", response_model=dict)
async def whatsapp_webhook(
    data: WhatsAppWebhook,
    db: AsyncSession = Depends(get_db),
):
    """Endpoint público para receber mensagens do WhatsApp."""
    bot = None
    if data.bot_id:
        result = await db.execute(select(Bot).where(Bot.id == data.bot_id))
        bot = result.scalar_one_or_none()

    if not bot:
        result = await db.execute(select(Bot).where(Bot.is_active == True).limit(1))
        bot = result.scalar_one_or_none()

    if not bot:
        return {"reply": "Bot não configurado. Entre em contato com o administrador."}

    if not bot.is_active:
        return {"reply": "Bot temporariamente indisponível."}

    chat_engine = ChatEngine(db, bot)
    result = await chat_engine.process_message(data.text)

    return {
        "reply": result["content"],
        "bot_id": str(bot.id),
        "type": result["type"],
    }
