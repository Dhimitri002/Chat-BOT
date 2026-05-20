"""License Schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LicenseValidateRequest(BaseModel):
    license_key: str = Field(..., pattern=r"^FLORA-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$")
    device_fingerprint: Optional[str] = None


class LicenseValidateResponse(BaseModel):
    valid: bool
    reason: Optional[str] = None
    plan: Optional[dict] = None
    expires_at: Optional[datetime] = None
    days_remaining: Optional[int] = None
    features: Optional[dict] = None


class LicenseResponse(BaseModel):
    id: str
    license_key: str
    status: str
    plan_name: str
    client_name: str
    expires_at: datetime
    days_remaining: int
    is_active: bool
    created_at: datetime


class LicenseCreateRequest(BaseModel):
    user_id: str
    plan_id: str
    days_valid: int = Field(default=30, ge=1, le=3650)
