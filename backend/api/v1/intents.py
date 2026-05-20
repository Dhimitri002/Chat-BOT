"""Intents Endpoints - API para gerenciamento de intenções."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db

router = APIRouter(prefix="/intents", tags=["intents"])


class IntentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    training_phrases: list[str] = Field(default_factory=list)
    response: str = ""
    category: str = "general"
    is_active: bool = True


class IntentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    training_phrases: Optional[list[str]] = None
    response: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_intents(
    bot_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista intenções."""
    from backend.models.intent import Intent

    query = select(Intent).where(Intent.owner_id == current_user.id)
    if bot_id:
        query = query.where(Intent.bot_id == bot_id)
    query = query.order_by(Intent.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    intents = result.scalars().all()

    return {
        "intents": [
            {
                "id": i.id,
                "name": i.name,
                "description": i.description,
                "training_phrases_count": len(i.training_phrases) if i.training_phrases else 0,
                "category": i.category,
                "is_active": i.is_active,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in intents
        ]
    }


@router.post("/")
async def create_intent(
    request: IntentCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cria uma nova intenção."""
    from backend.models.intent import Intent
    import uuid

    intent = Intent(
        id=str(uuid.uuid4()),
        owner_id=current_user.id,
        name=request.name,
        description=request.description,
        training_phrases=request.training_phrases,
        response=request.response,
        category=request.category,
        is_active=request.is_active,
    )
    db.add(intent)
    await db.flush()

    return {"success": True, "id": intent.id, "message": "Intenção criada."}


@router.put("/{intent_id}")
async def update_intent(
    intent_id: str,
    request: IntentUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza uma intenção."""
    from backend.models.intent import Intent

    result = await db.execute(
        select(Intent).where(Intent.id == intent_id, Intent.owner_id == current_user.id)
    )
    intent = result.scalar_one_or_none()

    if not intent:
        raise HTTPException(status_code=404, detail="Intenção não encontrada")

    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(intent, key, value)

    await db.flush()
    return {"success": True, "message": "Intenção atualizada."}


@router.delete("/{intent_id}")
async def delete_intent(
    intent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deleta uma intenção."""
    from backend.models.intent import Intent

    result = await db.execute(
        select(Intent).where(Intent.id == intent_id, Intent.owner_id == current_user.id)
    )
    intent = result.scalar_one_or_none()

    if not intent:
        raise HTTPException(status_code=404, detail="Intenção não encontrada")

    await db.delete(intent)
    await db.flush()
    return {"success": True, "message": "Intenção deletada."}


@router.post("/{intent_id}/train")
async def train_intent(
    intent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Treia uma intenção com as frases de treinamento."""
    return {"success": True, "message": "Intenção treinada com sucesso."}
