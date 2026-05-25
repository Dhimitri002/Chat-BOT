"""Bot Schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BotCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    system_prompt: str = Field(default="", min_length=0)
    personality: str = "friendly"
    language: str = "pt-BR"
    welcome_message: Optional[str] = "Olá! 👋 Como posso te ajudar?"
    farewell_message: Optional[str] = "Até mais! 👋"
    away_message: Optional[str] = None
    preferred_llm: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 500


class BotUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    personality: Optional[str] = None
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
    name: str
    description: str
    owner_id: str
    whatsapp_session_id: Optional[str]
    status: str
    system_prompt: str
    personality: str
    language: str
    welcome_message: Optional[str]
    farewell_message: Optional[str]
    error_message: Optional[str]
    command_prefix: str
    llm_model: str
    llm_provider: str
    llm_temperature: float
    llm_max_tokens: int
    config: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
