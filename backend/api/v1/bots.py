"""Bot Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from backend.database import get_db
from backend.schemas.bot import (
    BotCreateRequest, BotUpdateRequest, BotResponse,
    ChatRequest, ChatResponse, FloraChatRequest, FloraChatResponse,
    IntentCreate, IntentUpdate, IntentResponse,
)
from backend.models.bot import Bot
from backend.models.intent import Intent
from backend.models.user import User
from backend.core.chat_engine import process_message, process_flora_message
from backend.api.deps import get_current_user, require_admin
import uuid


class WhatsAppWebhook(BaseModel):
    text: str
    contact_id: str
    contact_name: str = "Usuario"
    bot_id: str = ""
    timestamp: str = ""


router = APIRouter(prefix="/bots", tags=["Bots"])


# ─── WhatsApp Webhook (MUST be before /{bot_id} routes) ───

@router.post("/chat", response_model=dict)
async def whatsapp_webhook(
    data: WhatsAppWebhook,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint for WhatsApp connector."""
    bot = None
    if data.bot_id:
        result = await db.execute(select(Bot).where(Bot.id == data.bot_id))
        bot = result.scalar_one_or_none()

    if not bot:
        result = await db.execute(select(Bot).where(Bot.is_active == True).limit(1))
        bot = result.scalar_one_or_none()

    if not bot:
        return {"reply": "Bot nao configurado. Entre em contato com o administrador."}

    intents_result = await db.execute(
        select(Intent).where(Intent.bot_id == bot.id, Intent.is_active == True)
    )
    intents = [
        {"tag": i.tag, "patterns": i.patterns, "responses": i.responses, "priority": i.priority}
        for i in intents_result.scalars().all()
    ]

    bot_config = {
        "prompt": bot.prompt,
        "has_llm": bool(bot.preferred_llm),
        "preferred_llm": bot.preferred_llm,
        "max_tokens": bot.max_tokens,
        "temperature": bot.temperature,
        "plan": "pro",
        "fallback_message": "Desculpa, nao entendi. Pode reformular?",
    }

    response = await process_message(data.text, intents, bot_config)
    return response


# ─── Bot CRUD (admin) ───

@router.post("/", response_model=dict, dependencies=[Depends(require_admin)])
async def create_bot(data: BotCreateRequest, db: AsyncSession = Depends(get_db)):
    bot = Bot(
        license_id=data.license_id,
        name=data.name,
        prompt=data.prompt,
        personality=data.personality,
        tone=data.tone,
        language=data.language,
        welcome_message=data.welcome_message,
        farewell_message=data.farewell_message,
        away_message=data.away_message,
        preferred_llm=data.preferred_llm,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
    )
    db.add(bot)
    await db.flush()
    return {"success": True, "bot": {"id": bot.id, "name": bot.name, "status": "created"}}


@router.get("/", response_model=dict, dependencies=[Depends(require_admin)])
async def list_bots(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bot).order_by(Bot.created_at.desc()))
    bots = result.scalars().all()
    return {
        "items": [
            {
                "id": b.id, "name": b.name, "is_active": b.is_active,
                "is_connected": b.is_connected, "personality": b.personality,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bots
        ],
        "total": len(bots),
    }


# ─── Bot by ID routes ───

@router.get("/{bot_id}", response_model=dict)
async def get_bot(bot_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {
        "id": bot.id, "name": bot.name, "prompt": bot.prompt,
        "personality": bot.personality, "tone": bot.tone,
        "language": bot.language, "welcome_message": bot.welcome_message,
        "is_active": bot.is_active, "is_connected": bot.is_connected,
        "preferred_llm": bot.preferred_llm, "temperature": bot.temperature,
        "max_tokens": bot.max_tokens, "version": bot.version,
    }


@router.put("/{bot_id}", response_model=dict, dependencies=[Depends(require_admin)])
async def update_bot(bot_id: str, data: BotUpdateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bot, key, value)
    bot.version += 1
    return {"success": True, "bot_id": bot.id, "version": bot.version}


# ─── Intents ───

@router.post("/{bot_id}/intents", response_model=dict, dependencies=[Depends(require_admin)])
async def create_intent(bot_id: str, data: IntentCreate, db: AsyncSession = Depends(get_db)):
    intent = Intent(
        bot_id=bot_id, tag=data.tag, patterns=data.patterns,
        responses=data.responses, priority=data.priority, is_active=data.is_active,
    )
    db.add(intent)
    await db.flush()
    return {"success": True, "intent": {"id": intent.id, "tag": intent.tag}}


@router.get("/{bot_id}/intents", response_model=dict)
async def list_intents(bot_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Intent).where(Intent.bot_id == bot_id).order_by(Intent.priority.desc()))
    intents = result.scalars().all()
    return {
        "items": [
            {"id": i.id, "tag": i.tag, "patterns": i.patterns,
             "responses": i.responses, "priority": i.priority, "is_active": i.is_active}
            for i in intents
        ],
    }


# ─── Sandbox Chat ───

@router.post("/{bot_id}/chat", response_model=dict)
async def chat_with_bot(
    bot_id: str, data: ChatRequest,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    """Test chat with a bot (sandbox)."""
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    intents_result = await db.execute(select(Intent).where(Intent.bot_id == bot_id, Intent.is_active == True))
    intents = [
        {"tag": i.tag, "patterns": i.patterns, "responses": i.responses, "priority": i.priority}
        for i in intents_result.scalars().all()
    ]

    bot_config = {
        "prompt": bot.prompt,
        "has_llm": bool(bot.preferred_llm),
        "preferred_llm": bot.preferred_llm,
        "max_tokens": bot.max_tokens,
        "temperature": bot.temperature,
        "plan": "pro",
        "fallback_message": "Desculpa, nao entendi. Pode reformular?",
    }
    response = await process_message(data.text, intents, bot_config)
    return response


# ─── Flora AI Chat ───

@router.post("/flora/chat", response_model=dict)
async def flora_chat(
    data: FloraChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Chat with Flora AI."""
    client_context = {
        "client_name": user.full_name or "Cliente",
        "plan_name": "Pro",
        "days_left": 30,
        "bot_status": "conectado",
        "plan": "pro",
    }
    response = await process_flora_message(data.message, client_context)
    return response
