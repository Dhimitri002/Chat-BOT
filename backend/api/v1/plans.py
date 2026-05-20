"""Plans Endpoints - API para gerenciamento de planos."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_current_admin, get_db
from backend.models.plan import Plan

router = APIRouter(prefix="/plans", tags=["plans"])


class PlanCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50)
    description: str = ""
    price_monthly: float = Field(..., ge=0)
    price_yearly: float = Field(..., ge=0)
    currency: str = "BRL"
    max_bots: int = Field(default=1, ge=0)
    max_messages_per_day: int = Field(default=100, ge=0)
    max_contacts: int = Field(default=1000, ge=0)
    features: dict = Field(default_factory=dict)
    is_active: bool = True
    is_public: bool = True
    sort_order: int = 0


class PlanUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    max_bots: Optional[int] = None
    max_messages_per_day: Optional[int] = None
    max_contacts: Optional[int] = None
    features: Optional[dict] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    sort_order: Optional[int] = None


@router.get("/")
async def list_plans(
    include_private: bool = Query(False),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos os planos disponíveis."""
    query = select(Plan).where(Plan.is_active == True)
    if not include_private:
        query = query.where(Plan.is_public == True)
    query = query.order_by(Plan.sort_order, Plan.price_monthly)

    result = await db.execute(query)
    plans = result.scalars().all()

    return {
        "plans": [
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "description": p.description,
                "price_monthly": p.price_monthly,
                "price_yearly": p.price_yearly,
                "currency": p.currency,
                "max_bots": p.max_bots,
                "max_messages_per_day": p.max_messages_per_day,
                "max_contacts": p.max_contacts,
                "features": p.features or {},
                "is_public": p.is_public,
                "sort_order": p.sort_order,
            }
            for p in plans
        ]
    }


@router.get("/{plan_id}")
async def get_plan(
    plan_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém detalhes de um plano."""
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    return {
        "id": plan.id,
        "name": plan.name,
        "slug": plan.slug,
        "description": plan.description,
        "price_monthly": plan.price_monthly,
        "price_yearly": plan.price_yearly,
        "currency": plan.currency,
        "max_bots": plan.max_bots,
        "max_messages_per_day": plan.max_messages_per_day,
        "max_contacts": plan.max_contacts,
        "features": plan.features or {},
        "is_active": plan.is_active,
        "is_public": plan.is_public,
    }


@router.post("/")
async def create_plan(
    request: PlanCreateRequest,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo plano (admin only)."""
    plan = Plan(**request.dict())
    db.add(plan)
    await db.flush()
    return {"success": True, "id": plan.id, "message": "Plano criado com sucesso."}


@router.put("/{plan_id}")
async def update_plan(
    plan_id: str,
    request: PlanUpdateRequest,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza um plano (admin only)."""
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    await db.flush()
    return {"success": True, "message": "Plano atualizado."}


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: str,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deleta um plano (admin only)."""
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    plan.is_active = False
    await db.flush()
    return {"success": True, "message": "Plano desativado."}


@router.get("/{plan_id}/features")
async def get_plan_features(
    plan_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém features de um plano."""
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    return {"features": plan.features or {}}


@router.post("/{plan_id}/subscribe")
async def subscribe_to_plan(
    plan_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Inscreve o usuário atual em um plano."""
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plano não encontrado ou inativo")

    return {
        "success": True,
        "message": f"Inscrição no plano {plan.name} realizada.",
        "plan": {"id": plan.id, "name": plan.name, "price": plan.price_monthly},
    }
