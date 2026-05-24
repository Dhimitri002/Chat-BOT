"""Users Endpoints — API para gerenciamento de usuários."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_current_admin, get_db
from backend.models.bot import Bot
from backend.models.message import Message
from backend.models.user import User
from backend.services.auth_service import hash_password, verify_password

router = APIRouter()


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


# ─── Perfil do usuário ────────────────────────────────────

@router.get("/me", response_model=dict)
async def get_me(current_user: User = Depends(get_current_user)):
    """Obtém perfil do usuário atual."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "avatar_url": current_user.avatar_url,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@router.put("/me", response_model=dict)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza perfil do usuário."""
    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return {
        "id": str(current_user.id),
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "message": "Perfil atualizado",
    }


@router.put("/me/password", response_model=dict)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Altera senha do usuário."""
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")

    current_user.hashed_password = hash_password(request.new_password)
    await db.commit()

    return {"message": "Senha alterada com sucesso" }


@router.delete("/me", response_model=dict)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deleta conta do usuário."""
    await db.delete(current_user)
    await db.commit()
    return {"message": "Conta deletada com sucesso"}


@router.get("/me/usage", response_model=dict)
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém estatísticas de uso do usuário."""
    # Contar bots
    bots_result = await db.execute(
        select(func.count()).where(Bot.user_id == current_user.id)
    )
    bots_count = bots_result.scalar() or 0

    # Contar mensagens
    messages_result = await db.execute(
        select(func.count())
        .select_from(Message)
        .join(Bot, Message.bot_id == Bot.id)
        .where(Bot.user_id == current_user.id)
    )
    messages_count = messages_result.scalar() or 0

    # Contar mensagens hoje
    from datetime import datetime, timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count())
        .select_from(Message)
        .join(Bot, Message.bot_id == Bot.id)
        .where(Bot.user_id == current_user.id)
        .where(Message.created_at >= today)
    )
    messages_today = today_result.scalar() or 0

    return {
        "bots_used": bots_count,
        "messages_total": messages_count,
        "messages_today": messages_today,
    }


# ─── Admin endpoints ──────────────────────────────────────

@router.get("/admin/users", response_model=dict, dependencies=[Depends(get_current_admin)])
async def admin_list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Lista todos os usuários (admin only)."""
    query = select(User)

    if search:
        query = query.where(
            User.email.contains(search) | User.full_name.contains(search)
        )

    # Count
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    # Page
    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(User.created_at.desc()).offset(offset).limit(per_page)
    )
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }
