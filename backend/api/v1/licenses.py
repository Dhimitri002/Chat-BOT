"""License Endpoints — API para gerenciamento de licenças."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_current_admin, get_db
from backend.models.user import User
from backend.services.license_service import LicenseService

router = APIRouter()


class LicenseActivateRequest(BaseModel):
    license_key: str = Field(..., min_length=10)


class LicenseValidateRequest(BaseModel):
    license_key: str = Field(..., min_length=10)


class LicenseCreateRequest(BaseModel):
    user_id: str
    plan_id: str
    duration_days: int = Field(default=30, ge=1, le=3650)


class LicenseRevokeRequest(BaseModel):
    license_id: str
    reason: str = ""


# ─── Endpoints do usuário ─────────────────────────────────

@router.get("/", response_model=dict)
async def list_licenses(
    active_only: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista licenças do usuário."""
    service = LicenseService()
    licenses = await service.get_user_licenses(db, str(current_user.id), active_only)

    return {
        "licenses": [
            {
                "id": str(lic.id),
                "license_key": lic.license_key[:8] + "..." + lic.license_key[-4:],
                "status": lic.status,
                "plan_id": str(lic.plan_id),
                "activated_at": lic.activated_at.isoformat() if lic.activated_at else None,
                "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
            }
            for lic in licenses
        ],
        "total": len(licenses),
    }


@router.post("/activate", response_model=dict)
async def activate_license(
    request: LicenseActivateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ativa uma licença para o usuário."""
    service = LicenseService()
    try:
        license_record = await service.activate_license(
            db, str(current_user.id), request.license_key
        )
        return {
            "message": "Licença ativada com sucesso",
            "license_id": str(license_record.id),
            "status": license_record.status,
            "expires_at": license_record.expires_at.isoformat() if license_record.expires_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{license_id}/validate", response_model=dict)
async def validate_license(
    license_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Valida uma licença."""
    service = LicenseService()
    license_record = await service.get_user_active_license(db, str(current_user.id))

    if not license_record:
        return {"valid": False, "reason": "no_active_license"}

    result = await service.validate_license(db, license_record.license_key)
    return result


@router.delete("/{license_id}")
async def deactivate_license(
    license_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Desativa uma licença."""
    service = LicenseService()
    success = await service.deactivate_license(db, license_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Licença não encontrada")
    return {"message": "Licença desativada"}


@router.get("/features", response_model=dict)
async def get_license_features(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém features disponíveis pela licença ativa."""
    service = LicenseService()
    features = await service.get_license_features(db, str(current_user.id))
    return features


# ─── Endpoints do admin ───────────────────────────────────

@router.post("/admin/generate", response_model=dict, dependencies=[Depends(get_current_admin)])
async def admin_generate_license(
    request: LicenseCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Gera uma nova licença (admin only)."""
    service = LicenseService()
    try:
        license_record = await service.generate_license(
            db, request.user_id, request.plan_id, request.duration_days
        )
        return {
            "license_key": license_record.license_key,
            "signature": license_record.signature,
            "status": license_record.status,
            "expires_at": license_record.expires_at.isoformat() if license_record.expires_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/revoke", response_model=dict, dependencies=[Depends(get_current_admin)])
async def admin_revoke_license(
    request: LicenseRevokeRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Revoga uma licença (admin only)."""
    service = LicenseService()
    success = await service.revoke_license(db, request.license_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Licença não encontrada")
    return {"message": "Licença revogada"}


@router.get("/admin/check-expired", response_model=dict, dependencies=[Depends(get_current_admin)])
async def admin_check_expired(
    db: AsyncSession = Depends(get_db),
):
    """Verifica e marca licenças expiradas (admin only)."""
    service = LicenseService()
    count = await service.check_expired_licenses(db)
    return {"expired_count": count, "message": f"{count} licenças marcadas como expiradas"}
