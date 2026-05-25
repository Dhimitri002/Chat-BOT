"""License Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class LicenseValidateRequest(BaseModel):
    license_key: str = Field(..., min_length=10, max_length=100)
    device_fingerprint: Optional[str] = ""


class LicenseValidateResponse(BaseModel):
    valid: bool
    reason: Optional[str] = None
    plan: Optional[dict] = None
    expires_at: Optional[str] = None
    days_remaining: Optional[int] = None
    features: Optional[dict] = None


class LicenseResponse(BaseModel):
    id: str
    license_key: str
    user_id: str
    plan_id: str
    status: str
    expires_at: Optional[datetime]
    days_remaining: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LicenseCreateRequest(BaseModel):
    user_id: str
    plan_id: str
    days_valid: int = Field(default=30, ge=1, le=3650)
