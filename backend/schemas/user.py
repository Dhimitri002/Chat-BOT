"""
Flora Platform — User Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=2, max_length=255)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[str] = Field(None, min_length=5, max_length=255)
    avatar_url: Optional[str] = None
    is_2fa_enabled: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    is_2fa_enabled: bool
    avatar_url: str
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    avatar_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserMinimal(BaseModel):
    id: str
    name: str
    email: str
