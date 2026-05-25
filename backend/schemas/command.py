"""Command Schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CommandCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    trigger: str = Field(..., min_length=1, max_length=50)
    response: str = ""
    response_type: str = "text"


class CommandUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[str] = None
    response: Optional[str] = None
    response_type: Optional[str] = None
    is_active: Optional[bool] = None


class CommandResponse(BaseModel):
    id: str
    bot_id: str
    name: str
    description: str
    trigger: str
    response: str
    response_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
