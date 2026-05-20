"""
Flora Platform — Command Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CommandCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = ""
    trigger: str = Field(..., min_length=1, max_length=100)
    response: str = ""
    response_type: str = "text"  # text, image, action


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
    use_count: int
    version: int
    created_at: datetime

    class Config:
        from_attributes = True


class CommandTest(BaseModel):
    message: str


class CommandTestResult(BaseModel):
    matched: bool
    command_name: str = ""
    trigger: str = ""
    response: str = ""
