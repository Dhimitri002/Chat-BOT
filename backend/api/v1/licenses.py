"""License Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.license import (
    LicenseValidateRequest, LicenseValidateResponse,
    LicenseCreateRequest, LicenseResponse,
)
from backend.services.license_service import create_license, validate_license
from backend.api.deps import get_current_user, require_admin
from backend.models.user import User

router = APIRouter(prefix="/licenses", tags=["Licenses"])


@router.post("/validate", response_model=dict)
async def validate(
    data: LicenseValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate a license key (public endpoint for client app)."""
    result = await validate_license(db, data.license_key, data.device_fingerprint)
    return result


@router.post("/", response_model=dict, dependencies=[Depends(require_admin)])
async def create(
    data: LicenseCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new license (admin only)."""
    lic = await create_license(db, data.user_id, data.plan_id, data.days_valid)
    return {
        "success": True,
        "license": {
            "id": lic.id,
            "license_key": lic.license_key,
            "status": lic.status,
            "expires_at": lic.expires_at.isoformat(),
        },
    }


@router.get("/", response_model=dict, dependencies=[Depends(require_admin)])
async def list_licenses(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, func
    from backend.models.license import License

    offset = (page - 1) * page_size
    result = await db.execute(
        select(License).order_by(License.created_at.desc()).offset(offset).limit(page_size)
    )
    licenses = result.scalars().all()

    count_result = await db.execute(select(func.count(License.id)))
    total = count_result.scalar()

    return {
        "items": [
            {
                "id": lic.id,
                "license_key": lic.license_key,
                "status": lic.status,
                "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
                "created_at": lic.created_at.isoformat() if lic.created_at else None,
            }
            for lic in licenses
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
