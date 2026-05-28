"""
Flora API v1 — Endpoints da Flora AI
======================================
Endpoints para interacao com a Flora AI:
  - Chat (enviar mensagem, receber resposta)
  - Sessoes (listar, ver historico, limpar)
  - Onboarding (passos do guia)
  - Help (ajuda por topico)
  - Sugestoes contextuais
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.services.flora_service import get_flora_service, FloraService
from backend.schemas.flora import (
    ChatRequest,
    ChatResponse,
    SessionHistoryResponse,
    SessionInfoResponse,
    SessionListResponse,
    SessionDeleteResponse,
    OnboardingStateSchema,
    OnboardingStepResponse,
    OnboardingProgressRequest,
    HelpTopicRequest,
    HelpTopicSchema,
    HelpTopicListResponse,
    SuggestionsResponse,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flora", tags=["Flora AI"])


# ─── Chat ──────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def flora_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Envia uma mensagem para a Flora AI e recebe uma resposta.

    - Se `session_id` for omitido, uma nova sessao e criada.
    - A Flora detecta a intencao do usuario e responde de forma contextual.
    - Quando o LLM nao esta disponivel, usa respostas baseadas em regras.
    """
    service = get_flora_service()

    result = await service.chat(
        message=request.message,
        session_id=request.session_id,
        user_id=str(current_user.id),
        user_name=current_user.name or "Usuario",
        user_plan="free",  # TODO: get from subscription
    )

    return ChatResponse(
        response=result["response"],
        session_id=result["session_id"],
        intent=result["intent"],
        confidence=result["confidence"],
        tools_used=result.get("tools_used", []),
        is_new_session=result["is_new_session"],
        message_count=result["message_count"],
        timestamp=result["timestamp"],
    )


# ─── Sessions ──────────────────────────────────────────────────────────

@router.get("/sessions", response_model=SessionListResponse)
async def list_flora_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    """
    Lista todas as sessoes Flora do usuario atual.
    """
    # Query database for user's Flora sessions
    from backend.models.flora_session import FloraSession
    result = await db.execute(
        select(FloraSession)
        .where(FloraSession.user_id == current_user.id)
        .where(FloraSession.is_active == True)
        .order_by(FloraSession.last_activity.desc())
    )
    sessions = result.scalars().all()

    session_infos = []
    for s in sessions:
        session_infos.append(SessionInfoResponse(
            session_id=s.session_id,
            user_id=s.user_id,
            user_name=current_user.name or "",
            user_plan="free",
            message_count=s.message_count,
            total_tokens=s.tokens_used,
            is_onboarding=False,
            onboarding_step=0,
            last_intent="",
            created_at=s.created_at.isoformat() if s.created_at else "",
            updated_at=s.last_activity.isoformat() if s.last_activity else "",
            is_expired=False,
        ))

    return SessionListResponse(sessions=session_infos, total=len(session_infos))


@router.get("/sessions/{session_id}", response_model=SessionHistoryResponse)
async def get_flora_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionHistoryResponse:
    """
    Retorna o historico completo de uma sessao Flora.
    """
    service = get_flora_service()
    history = service.get_history(session_id)

    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"Sessao '{session_id}' nao encontrada",
        )

    # Get token count from DB
    from backend.models.flora_session import FloraSession
    result = await db.execute(
        select(FloraSession).where(FloraSession.session_id == session_id)
    )
    db_session = result.scalar_one_or_none()
    total_tokens = db_session.tokens_used if db_session else 0

    return SessionHistoryResponse(
        session_id=session_id,
        messages=history,
        message_count=len(history),
        total_tokens=total_tokens,
    )


@router.delete("/sessions/{session_id}", response_model=SessionDeleteResponse)
async def delete_flora_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionDeleteResponse:
    """
    Remove uma sessao Flora completamente.
    """
    service = get_flora_service()

    # Try in-memory first
    deleted = service.delete_session(session_id)

    # Also mark as inactive in DB
    from backend.models.flora_session import FloraSession
    result = await db.execute(
        select(FloraSession).where(FloraSession.session_id == session_id)
    )
    db_session = result.scalar_one_or_none()
    if db_session:
        db_session.is_active = False
        await db.commit()
        deleted = True

    if not deleted and not db_session:
        raise HTTPException(
            status_code=404,
            detail=f"Sessao '{session_id}' nao encontrada",
        )

    return SessionDeleteResponse(
        success=True,
        message="Sessao removida com sucesso",
        session_id=session_id,
    )


@router.post("/sessions/{session_id}/clear", response_model=SessionDeleteResponse)
async def clear_flora_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionDeleteResponse:
    """
    Limpa o historico de uma sessao (mantem a sessao ativa).
    """
    service = get_flora_service()
    cleared = service.clear_history(session_id)

    if not cleared:
        raise HTTPException(
            status_code=404,
            detail=f"Sessao '{session_id}' nao encontrada",
        )

    return SessionDeleteResponse(
        success=True,
        message="Historico limpo com sucesso",
        session_id=session_id,
    )


# ─── Onboarding ────────────────────────────────────────────────────────

@router.get("/onboarding", response_model=OnboardingStateSchema)
async def get_onboarding_state(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OnboardingStateSchema:
    """
    Retorna o estado atual do onboarding para o usuario.
    """
    service = get_flora_service()
    steps = service.get_onboarding_steps()

    step_schemas = []
    for step in steps:
        step_schemas.append({
            "step": step["step"],
            "title": step["title"],
            "description": step["description"],
            "action": step["action"],
            "emoji": step["emoji"],
            "is_completed": False,
        })

    return OnboardingStateSchema(
        is_onboarding=True,
        current_step=1,
        completed_steps=[],
        steps=step_schemas,
    )


@router.get("/onboarding/step/{step_number}", response_model=OnboardingStepResponse)
async def get_onboarding_step(
    step_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OnboardingStepResponse:
    """
    Retorna o conteudo detalhado de um passo do onboarding.
    """
    if step_number < 1 or step_number > 6:
        raise HTTPException(
            status_code=400,
            detail="Passo deve ser entre 1 e 6",
        )

    service = get_flora_service()
    step_data = service.get_onboarding_step(step_number)

    if not step_data:
        raise HTTPException(
            status_code=404,
            detail=f"Passo {step_number} nao encontrado",
        )

    return OnboardingStepResponse(**step_data)


@router.post("/onboarding/progress", response_model=OnboardingStepResponse)
async def progress_onboarding(
    request: OnboardingProgressRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OnboardingStepResponse:
    """
    Avanca o onboarding para o proximo passo ou um passo especifico.

    Acoes:
    - `advance`: vai para o proximo passo
    - `go_to`: vai para `target_step`
    - `skip`: pula o passo atual
    """
    service = get_flora_service()

    # Determine target step
    if request.action == "go_to" and request.target_step:
        target = request.target_step
    else:
        # Default: step 1 (simplified — in production, track per-user state)
        target = 1

    step_data = service.get_onboarding_step(target)
    if not step_data:
        raise HTTPException(status_code=404, detail="Passo nao encontrado")

    return OnboardingStepResponse(**step_data)


# ─── Help ──────────────────────────────────────────────────────────────

@router.get("/help", response_model=HelpTopicListResponse)
async def list_help_topics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HelpTopicListResponse:
    """
    Lista todos os topicos de ajuda disponiveis.
    """
    service = get_flora_service()
    all_topics = service.get_all_help_topics()

    topics_list = []
    for key, data in all_topics.items():
        topics_list.append({
            "topic": key,
            "title": data["title"],
            "preview": data["content"][:100] + "...",
        })

    return HelpTopicListResponse(topics=topics_list)


@router.get("/help/{topic}", response_model=HelpTopicSchema)
async def get_help_topic(
    topic: str,
    question: Optional[str] = Query(None, description="Pergunta especifica sobre o topico"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HelpTopicSchema:
    """
    Retorna conteudo de ajuda detalhado para um topico.

    Topicos disponiveis:
    - `general`: Ajuda geral
    - `bot_creation`: Criacao de bots
    - `whatsapp_connection`: Conexao WhatsApp
    - `plans`: Planos e precos
    - `onboarding`: Guia de onboarding
    """
    service = get_flora_service()
    help_data = service.get_help_topic(topic)

    if not help_data:
        raise HTTPException(
            status_code=404,
            detail=f"Topico '{topic}' nao encontrado. Topicos disponiveis: general, bot_creation, whatsapp_connection, plans, onboarding",
        )

    return HelpTopicSchema(
        topic=help_data["topic"],
        title=help_data["title"],
        content=help_data["content"],
        related_topics=help_data.get("related", []),
    )


# ─── Suggestions ───────────────────────────────────────────────────────

@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(
    session_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuggestionsResponse:
    """
    Retorna sugestoes contextuais para o usuario.
    Baseado no estado atual da conversa.
    """
    service = get_flora_service()
    suggestions = service.get_suggestions(session_id)

    return SuggestionsResponse(
        suggestions=suggestions,
        context=session_id or "default",
    )
