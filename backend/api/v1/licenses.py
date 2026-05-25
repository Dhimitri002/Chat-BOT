"""Flora Platform — License Management Endpoints"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_current_admin, get_db
from backend.models.license import License
from backend.models.user import User
from backend.schemas.license import (
    LicenseValidateRequest,
    LicenseValidateResponse,
    LicenseResponse,
    LicenseCreateRequest,
)
from backend.services.license_service import LicenseService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/licenses", tags=["licenses"])


@router.post("/validate", response_model=LicenseValidateResponse)
async def validate_license(
    body: LicenseValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate a license key."""
    result = await LicenseService().validate_license(
        db,
        body.license_key,
        body.device_fingerprint or "",
    )

    if not result["valid"]:
        return LicenseValidateResponse(valid=False, reason=result.get("reason"))

    # Get plan info
    from backend.models.plan import Plan
    plan_result = await db.execute(select(Plan).where(Plan.id == result["plan_id"]))
    plan = plan_result.scalar_one_or_none()

    return LicenseValidateResponse(
        valid=True,
        plan={"id": str(plan.id), "name": plan.name, "features": plan.features} if plan else None,
        expires_at=result.get("expires_at"),
        days_remaining=result.get("days_remaining"),
        features=plan.features if plan else None,
    )


@router.post("/activate")
async def activate_license(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate a license for the current user."""
    license_key = body.get("license_key", "")
    hardware_fingerprint = body.get("hardware_fingerprint", "")
    machine_id = body.get("machine_id", "")

    if not license_key:
        raise HTTPException(status_code=400, detail="Chave de licença obrigatória")

    result = await LicenseService().activate_license(
        db, license_key, str(current_user.id), hardware_fingerprint, machine_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("reason", "Erro ao ativar licença"))

    await db.commit()
    return result


@router.get("")
async def list_my_licenses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(False),
):
    """List all licenses for the current user."""
    licenses = await LicenseService().get_user_licenses(db, str(current_user.id), active_only)
    return {
        "licenses": [
            {
                "id": str(l.id),
                "license_key": l.license_key[:12] + "...",
                "status": l.status,
                "plan_id": str(l.plan_id),
                "expires_at": l.expires_at.isoformat() if l.expires_at else None,
                "days_remaining": l.days_remaining,
                "is_active": l.is_active,
                "created_at": l.created_at.isoformat(),
            }
            for l in licenses
        ],
        "total": len(licenses),
    }


# ─── Admin License Management ───────────────────────────────────────

@router.post("/admin/generate", dependencies=[Depends(get_current_admin)])
async def admin_generate_license(
    body: LicenseCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a new license (admin only)."""
    lic = await LicenseService().generate_license(
        db=db,
        user_id=body.user_id,
        plan_id=body.plan_id,
        duration_days=body.days_valid,
    )
    await db.commit()
    return {
        "id": str(lic.id),
        "license_key": lic.license_key,
        "status": lic.status,
        "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
    }


@router.post("/admin/revoke/{license_id}", dependencies=[Depends(get_current_admin)])
async def admin_revoke_license(
    license_id: str,
    reason: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a license (admin only)."""
    success = await LicenseService().revoke_license(db, license_id, reason)
    if not success:
        raise HTTPException(status_code=404, detail="Licença não encontrada")
    await db.commit()
    return {"success": True, "message": "Licença revogada"}


@router.get("/admin/all", dependencies=[Depends(get_current_admin)])
async def admin_list_all_licenses(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(""),
):
    """List all licenses (admin only)."""
    query = select(License).join(User, License.user_id == User.id)
    count_query = select(func.count(License.id))

    if status:
        query = query.where(License.status == status)
        count_query = count_query.where(License.status == status)

    total = (await db.execute(count_query)).scalar()
    query = query.order_by(License.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    licenses = result.scalars().all()

    return {
        "licenses": [
            {
                "id": str(l.id),
                "license_key": l.license_key[:12] + "...",
                "user_id": str(l.user_id),
                "plan_id": str(l.plan_id),
                "status": l.status,
                "expires_at": l.expires_at.isoformat() if l.expires_at else None,
                "created_at": l.created_at.isoformat(),
            }
            for l in licenses
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
