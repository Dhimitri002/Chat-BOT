"""
Flora Platform — Intent Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class IntentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = ""
    keywords: List[str] = []
    responses: List[str] = []
    priority: int = 0


class IntentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    responses: Optional[List[str]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class IntentResponse(BaseModel):
    id: str
    bot_id: str
    name: str
    description: str
    keywords: List[str]
    responses: List[str]
    priority: int
    is_active: bool
    match_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class IntentTest(BaseModel):
    message: str


class IntentTestResult(BaseModel):
    matched: bool
    intent_name: str = ""
    confidence: float = 0.0
    response: str = ""
