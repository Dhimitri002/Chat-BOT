"""Bot Schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BotCreateRequest(BaseModel):
    license_id: str
    name: str = Field(..., min_length=1, max_length=100)
    prompt: str = Field(..., min_length=10)
    personality: str = "friendly"
    tone: str = "warm"
    language: str = "pt-BR"
    welcome_message: Optional[str] = None
    farewell_message: Optional[str] = None
    away_message: Optional[str] = None
    preferred_llm: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024


class BotUpdateRequest(BaseModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    personality: Optional[str] = None
    tone: Optional[str] = None
    language: Optional[str] = None
    welcome_message: Optional[str] = None
    farewell_message: Optional[str] = None
    away_message: Optional[str] = None
    preferred_llm: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None


class BotResponse(BaseModel):
    id: str
    license_id: str
    name: str
    prompt: str
    personality: str
    tone: str
    language: str
    welcome_message: Optional[str]
    is_active: bool
    is_connected: bool
    preferred_llm: Optional[str]
    temperature: float
    max_tokens: int
    version: int
    created_at: datetime
    updated_at: datetime


class ChatRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)


class ChatResponse(BaseModel):
    reply: str
    source: str  # "intent" | "llm" | "fallback"
    metadata: dict = {}


class FloraChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None


class FloraChatResponse(BaseModel):
    reply: str
    session_id: str
    tokens_used: int = 0


class IntentCreate(BaseModel):
    tag: str = Field(..., min_length=1, max_length=100)
    patterns: list[str] = Field(..., min_length=1)
    responses: list[str] = Field(..., min_length=1)
    priority: int = 0
    is_active: bool = True


class IntentUpdate(BaseModel):
    tag: Optional[str] = None
    patterns: Optional[list[str]] = None
    responses: Optional[list[str]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class IntentResponse(BaseModel):
    id: str
    bot_id: str
    tag: str
    patterns: list[str]
    responses: list[str]
    priority: int
    is_active: bool
    created_at: datetime
