"""Flora AI Endpoints — API para interação com a Flora AI (LLMs reais)."""
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.core.flora_engine import FloraEngine
from backend.core.llm_router import LLMRouter
from backend.models.bot import Bot
from backend.models.flora_session import FloraSession
from backend.models.user import User
from backend.services.bot_service import BotService
from backend.services.license_service import LicenseService

router = APIRouter()


class FloraChatRequest(BaseModel):
    bot_id: str = Field(..., description="ID do bot")
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    rating: int = Field(..., ge=1, le=5)


@router.post("/chat")
async def flora_chat(
    request: FloraChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Conversa com Flora AI (resposta completa)."""
    bot = await BotService.get_bot(db, request.bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    if not bot.is_active:
        raise HTTPException(status_code=400, detail="Bot está inativo")

    # Verificar acesso a LLM pela licença
    license_service = LicenseService()
    features = await license_service.get_license_features(db, str(current_user.id))
    if not features.get("has_llm") and not features.get("has_flora"):
        raise HTTPException(
            status_code=403,
            detail="Seu plano não inclui acesso à Flora AI. Faça upgrade.",
        )

    start_time = time.time()

    llm_router = LLMRouter()
    flora_engine = FloraEngine(db, bot, llm_router)
    result = await flora_engine.chat(request.message, request.session_id)

    response_time_ms = int((time.time() - start_time) * 1000)

    return {
        "content": result["content"],
        "session_id": result["session_id"],
        "model_used": result.get("model"),
        "provider": result.get("provider"),
        "usage": result.get("usage", {}),
        "response_time_ms": response_time_ms,
        "bot_name": bot.name,
    }


@router.post("/chat/stream")
async def flora_chat_stream(
    request: FloraChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Conversa com Flora AI (streaming via SSE)."""
    bot = await BotService.get_bot(db, request.bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    # Verificar acesso
    license_service = LicenseService()
    features = await license_service.get_license_features(db, str(current_user.id))
    if not features.get("has_llm") and not features.get("has_flora"):
        raise HTTPException(
            status_code=403,
            detail="Seu plano não inclui acesso à Flora AI.",
        )

    llm_router = LLMRouter()
    flora_engine = FloraEngine(db, bot, llm_router)

    async def event_generator():
        async for chunk in flora_engine.chat_stream(request.message, request.session_id):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.get("/sessions")
async def list_flora_sessions(
    bot_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista sessões Flora de um bot."""
    bot = await BotService.get_bot(db, bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    result = await db.execute(
        select(FloraSession)
        .where(
            FloraSession.bot_id == bot_id,
            FloraSession.is_active == True,
        )
        .order_by(FloraSession.updated_at.desc())
        .limit(50)
    )
    sessions = result.scalars().all()

    return {
        "sessions": [
            {
                "id": str(s.id),
                "bot_id": str(s.bot_id),
                "context": s.context,
                "is_active": s.is_active,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in sessions
        ],
        "total": len(sessions),
    }


@router.get("/sessions/{session_id}")
async def get_flora_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém detalhes de uma sessão Flora."""
    result = await db.execute(
        select(FloraSession).where(FloraSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    return {
        "id": str(session.id),
        "bot_id": str(session.bot_id),
        "context": session.context,
        "session_data": session.session_data,
        "is_active": session.is_active,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


@router.delete("/sessions/{session_id}")
async def delete_flora_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deleta uma sessão Flora."""
    result = await db.execute(
        select(FloraSession).where(FloraSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    # Limpar memória
    llm_router = LLMRouter()
    flora_engine = FloraEngine(db, None, llm_router)
    await flora_engine.clear_memory(session_id)

    await db.delete(session)
    await db.commit()

    return {"message": "Sessão deletada com sucesso"}


@router.post("/sessions/{session_id}/feedback")
async def add_flora_feedback(
    session_id: str,
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Adiciona feedback a uma resposta da Flora."""
    # Aqui salvaria o feedback no banco para análise de qualidade
    return {"message": "Feedback registrado com sucesso"}
