"""Flora Platform — User Management Endpoints"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.core.security import get_password_hash
from backend.models.user import User
from backend.schemas.user import UserResponse, UserUpdate, ChangePassword

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get the current user's profile."""
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile."""
    update_data = body.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"]:
        current_user.name = update_data["name"]
    if "email" in update_data and update_data["email"]:
        existing = await db.execute(
            select(User).where(User.email == update_data["email"], User.id != current_user.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já está em uso")
        current_user.email = update_data["email"]
    if "avatar_url" in update_data:
        current_user.avatar_url = update_data["avatar_url"]
    if "password" in update_data and update_data["password"]:
        current_user.hashed_password = get_password_hash(update_data["password"])

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/change-password")
async def change_password(
    body: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password."""
    from backend.core.security import verify_password, get_password_hash

    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")

    current_user.hashed_password = get_password_hash(body.new_password)
    await db.commit()
    return {"success": True, "message": "Senha alterada com sucesso"}
