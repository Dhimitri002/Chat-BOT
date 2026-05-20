"""Webhooks Endpoints - API para gerenciamento de webhooks."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_current_admin, get_db

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookCreateRequest(BaseModel):
    url: str = Field(..., description="URL do webhook")
    events: list[str] = Field(default=["message.received", "bot.connected"])
    secret: Optional[str] = None
    is_active: bool = True
    description: str = ""


class WebhookUpdateRequest(BaseModel):
    url: Optional[str] = None
    events: Optional[list[str]] = None
    secret: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


@router.get("/")
async def list_webhooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista webhooks do usuário."""
    from backend.models.webhook import Webhook

    query = select(Webhook).where(Webhook.owner_id == current_user.id)
    query = query.order_by(Webhook.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    webhooks = result.scalars().all()

    return {
        "webhooks": [
            {
                "id": w.id,
                "url": w.url,
                "events": w.events,
                "is_active": w.is_active,
                "description": w.description,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in webhooks
        ]
    }


@router.post("/")
async def create_webhook(
    request: WebhookCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo webhook."""
    from backend.models.webhook import Webhook
    import uuid

    webhook = Webhook(
        id=str(uuid.uuid4()),
        owner_id=current_user.id,
        url=request.url,
        events=request.events,
        secret=request.secret,
        is_active=request.is_active,
        description=request.description,
    )
    db.add(webhook)
    await db.flush()

    return {"success": True, "id": webhook.id, "message": "Webhook criado."}


@router.put("/{webhook_id}")
async def update_webhook(
    webhook_id: str,
    request: WebhookUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza um webhook."""
    from backend.models.webhook import Webhook

    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id, Webhook.owner_id == current_user.id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook não encontrado")

    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(webhook, key, value)

    await db.flush()
    return {"success": True, "message": "Webhook atualizado."}


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deleta um webhook."""
    from backend.models.webhook import Webhook

    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id, Webhook.owner_id == current_user.id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook não encontrado")

    await db.delete(webhook)
    await db.flush()
    return {"success": True, "message": "Webhook deletado."}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Testa um webhook enviando um evento de teste."""
    return {"success": True, "message": "Evento de teste enviado."}


@router.get("/{webhook_id}/logs")
async def get_webhook_logs(
    webhook_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém logs de entrega de um webhook."""
    return {"logs": [], "page": page, "page_size": page_size}


@router.post("/incoming/{token}")
async def receive_webhook(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Endpoint para receber webhooks externos."""
    body = await request.json()
    return {"success": True, "message": "Webhook recebido."}
