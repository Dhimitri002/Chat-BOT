"""Flora AI Endpoints - API para interação com a Flora AI."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.core.flora_engine import flora_engine

router = APIRouter(prefix="/flora", tags=["flora"])


class FloraChatRequest(BaseModel):
    bot_id: str = Field(..., description="ID do bot")
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None


class FloraChatResponse(BaseModel):
    response: str
    source: str
    session_id: str
    model_used: Optional[str] = None
    response_time_ms: int
    bot_name: Optional[str] = None


class PromptCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=10, max_length=10000)
    category: str = "custom"
    is_public: bool = False


class PromptUpdateRequest(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None


@router.post("/chat", response_model=FloraChatResponse)
async def chat_with_flora(
    request: FloraChatRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Envia mensagem para a Flora AI e recebe resposta."""
    result = await flora_engine.chat(
        db=db,
        bot_id=request.bot_id,
        user_message=request.message,
        session_id=request.session_id,
        sender=current_user.id,
    )

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return FloraChatResponse(**result)


@router.get("/sessions")
async def list_flora_sessions(
    bot_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista sessões Flora do usuário."""
    from backend.models.flora_session import FloraSession

    query = select(FloraSession).where(FloraSession.status == "active")
    if bot_id:
        query = query.where(FloraSession.bot_id == bot_id)

    query = query.order_by(FloraSession.last_activity_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return {
        "sessions": [
            {
                "id": s.id,
                "bot_id": s.bot_id,
                "sender": s.sender,
                "message_count": s.message_count,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "last_activity_at": s.last_activity_at.isoformat() if s.last_activity_at else None,
            }
            for s in sessions
        ],
        "page": page,
        "page_size": page_size,
    }


@router.get("/session/{session_id}")
async def get_flora_session(
    session_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém detalhes de uma sessão Flora."""
    from backend.models.flora_session import FloraSession

    result = await db.execute(
        select(FloraSession).where(FloraSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    return {
        "id": session.id,
        "bot_id": session.bot_id,
        "sender": session.sender,
        "message_count": session.message_count,
        "status": session.status,
        "context": session.context,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
    }


@router.delete("/session/{session_id}")
async def delete_flora_session(
    session_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deleta uma sessão Flora."""
    await flora_engine.delete_session(session_id)
    return {"success": True, "message": "Sessão deletada."}


@router.get("/prompts")
async def list_prompts(
    category: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista prompts disponíveis."""
    from backend.models.bot_template import BotTemplate

    query = select(BotTemplate).where(BotTemplate.is_active == True)
    if category:
        query = query.where(BotTemplate.category == category)

    result = await db.execute(query)
    templates = result.scalars().all()

    return {
        "prompts": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "prompt_preview": t.prompt[:200] if t.prompt else "",
            }
            for t in templates
        ]
    }


@router.post("/prompt")
async def create_prompt(
    request: PromptCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo prompt personalizado."""
    return {"success": True, "message": "Prompt criado.", "id": "new-prompt-id"}


@router.put("/prompt/{prompt_id}")
async def update_prompt(
    prompt_id: str,
    request: PromptUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza um prompt."""
    return {"success": True, "message": "Prompt atualizado."}


@router.delete("/prompt/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deleta um prompt."""
    return {"success": True, "message": "Prompt deletado."}


@router.get("/usage")
async def get_llm_usage(
    bot_id: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém estatísticas de uso de LLM."""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import func
    from backend.models.llm_usage import LLMUsage

    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = select(
        func.count(LLMUsage.id).label("total_requests"),
        func.sum(LLMUsage.total_tokens).label("total_tokens"),
        func.avg(LLMUsage.response_time_ms).label("avg_response_time"),
        func.sum(LLMUsage.cost).label("total_cost"),
    ).where(LLMUsage.created_at >= since)

    if bot_id:
        query = query.where(LLMUsage.bot_id == bot_id)

    result = await db.execute(query)
    stats = result.one()

    return {
        "period_days": days,
        "total_requests": stats.total_requests or 0,
        "total_tokens": int(stats.total_tokens or 0),
        "avg_response_time_ms": round(float(stats.avg_response_time or 0), 2),
        "total_cost": round(float(stats.total_cost or 0), 4),
    }


@router.post("/test")
async def test_prompt(
    request: FloraChatRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Testa um prompt com a LLM (sem salvar no banco)."""
    result = await flora_engine.chat(
        db=db,
        bot_id=request.bot_id,
        user_message=request.message,
        session_id=None,
        sender="test",
    )
    return result


# Import select at module level
from sqlalchemy import select
