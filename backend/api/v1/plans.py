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
    query = query.order_by(Plan.sort_order.asc(), Plan.price_monthly.asc())
    result = await db.execute(query)
    plans = result.scalars().all()

    return {
        "plans": [
            {
                "id": str(p.id),
                "name": p.name,
                "slug": p.slug,
                "description": p.description,
                "price_monthly": p.price_monthly,
                "price_yearly": p.price_yearly,
                "currency": p.currency,
                "max_bots": p.max_bots,
                "max_messages_per_day": p.max_messages_per_day,
                "max_contacts": p.max_contacts,
                "features": p.features,
                "is_public": p.is_public,
                "sort_order": p.sort_order,
            }
            for p in plans
        ],
        "total": len(plans),
    }


@router.get("/{plan_id}")
async def get_plan(
    plan_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific plan by ID."""
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return {
        "id": str(plan.id),
        "name": plan.name,
        "slug": plan.slug,
        "description": plan.description,
        "price_monthly": plan.price_monthly,
        "price_yearly": plan.price_yearly,
        "currency": plan.currency,
        "max_bots": plan.max_bots,
        "max_messages_per_day": plan.max_messages_per_day,
        "max_contacts": plan.max_contacts,
        "features": plan.features,
        "is_public": plan.is_public,
        "sort_order": plan.sort_order,
    }


@router.post("/", dependencies=[Depends(get_current_admin)])
async def create_plan(
    body: PlanCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new plan (admin only)."""
    import uuid
    plan = Plan(
        id=str(uuid.uuid4()),
        name=body.name,
        slug=body.slug,
        description=body.description,
        price_monthly=body.price_monthly,
        price_yearly=body.price_yearly,
        currency=body.currency,
        max_bots=body.max_bots,
        max_messages_per_day=body.max_messages_per_day,
        max_contacts=body.max_contacts,
        features=body.features,
        is_active=body.is_active,
        is_public=body.is_public,
        sort_order=body.sort_order,
    )
    db.add(plan)
    await db.commit()
    return {"id": str(plan.id), "name": plan.name}


@router.put("/{plan_id}", dependencies=[Depends(get_current_admin)])
async def update_plan(
    plan_id: str,
    body: PlanUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a plan (admin only)."""
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(plan, field) and value is not None:
            setattr(plan, field, value)

    await db.commit()
    return {"success": True, "message": "Plano atualizado"}


@router.delete("/{plan_id}", dependencies=[Depends(get_current_admin)])
async def delete_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a plan (admin only)."""
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    await db.delete(plan)
    await db.commit()
    return {"success": True, "message": "Plano removido"}
