"""Auth Schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    name: Optional[str] = Field(None, max_length=255)


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional["UserResponse"] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class TwoFAVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    is_active: bool
    is_2fa_enabled: bool
    created_at: str
