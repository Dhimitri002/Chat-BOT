"""
Flora API v1 — Endpoints da Flora AI
======================================
Endpoints para interação com a Flora AI:
  - Chat (enviar mensagem, receber resposta)
  - Histórico (ver, limpar)
  - Onboarding (passos do guia)
  - Help (ajuda por tópico)
  - Sugestões contextuais
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.models.flora_session import FloraSession
from backend.services.flora_service import get_flora_service, FloraService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

router = APIRouter(prefix="/flora", tags=["Flora AI"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = Field(None)


class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    confidence: float
    tools_used: list[dict] = []
    is_new_session: bool = False
    message_count: int = 0
    timestamp: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[dict]
    message_count: int
    total_tokens: int


class OnboardingStep(BaseModel):
    id: str
    title: str
    description: str
    icon: str
    action: Optional[str]


class HelpRequest(BaseModel):
    topic: str
    question: Optional[str] = None


class HelpResponse(BaseModel):
    topic: str
    title: str
    content: str
    related_topics: list[str] = []


class SuggestionsResponse(BaseModel):
    suggestions: list[str]


@router.post("/chat", response_model=ChatResponse)
async def flora_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    flora_service: FloraService = Depends(get_flora_service),
):
    """Envia mensagem para a Flora AI e recebe resposta."""
    try:
        result = await flora_service.chat(
            message=request.message,
            session_id=request.session_id,
            user_id=str(current_user.id),
            user_name=current_user.name,
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar mensagem: {str(e)}")


@router.get("/history", response_model=HistoryResponse)
async def flora_history(
    session_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    flora_service: FloraService = Depends(get_flora_service),
):
    history = flora_service.get_history(session_id)
    session_info = flora_service.get_session_info(session_id)
    if not history and not session_info:
        raise HTTPException(status_code=404, detail=f"Sessão '{session_id}' não encontrada")
    return HistoryResponse(
        session_id=session_id,
        messages=history,
        message_count=session_info["message_count"] if session_info else 0,
        total_tokens=session_info["total_tokens"] if session_info else 0,
    )


@router.delete("/history")
async def flora_clear_history(
    session_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    flora_service: FloraService = Depends(get_flora_service),
):
    cleared = flora_service.clear_history(session_id)
    if not cleared:
        raise HTTPException(status_code=404, detail=f"Sessão '{session_id}' não encontrada")
    return {"success": True, "message": "Histórico limpo com sucesso", "session_id": session_id}


@router.get("/onboarding")
async def flora_onboarding(
    current_user: User = Depends(get_current_user),
    flora_service: FloraService = Depends(get_flora_service),
):
    steps = flora_service.get_onboarding_steps()
    return steps


@router.post("/help", response_model=HelpResponse)
async def flora_help(
    request: HelpRequest,
    current_user: User = Depends(get_current_user),
    flora_service: FloraService = Depends(get_flora_service),
):
    help_content = flora_service.get_help_topic(request.topic)
    if not help_content:
        raise HTTPException(status_code=404, detail=f"Tópico '{request.topic}' não encontrado")
    return HelpResponse(
        topic=request.topic,
        title=help_content.get("title", request.topic),
        content=help_content.get("content", "Conteúdo não disponível"),
        related_topics=help_content.get("related", []),
    )


@router.get("/suggestions", response_model=SuggestionsResponse)
async def flora_suggestions(
    session_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    flora_service: FloraService = Depends(get_flora_service),
):
    suggestions = flora_service.get_suggestions(session_id)
    return SuggestionsResponse(suggestions=suggestions)


@router.get("/sessions/{session_id}")
async def flora_session_info(
    session_id: str,
    current_user: User = Depends(get_current_user),
    flora_service: FloraService = Depends(get_flora_service),
):
    info = flora_service.get_session_info(session_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Sessão '{session_id}' não encontrada")
    return info


@router.delete("/sessions/{session_id}")
async def flora_delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    flora_service: FloraService = Depends(get_flora_service),
):
    deleted = flora_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Sessão '{session_id}' não encontrada")
    return {"success": True, "message": "Sessão excluída com sucesso", "session_id": session_id}
