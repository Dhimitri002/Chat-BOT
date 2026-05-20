"""
Flora Platform — Plan Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PlanCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=50)
    description: str = ""
    price_monthly: float = Field(..., ge=0)
    price_yearly: float = Field(..., ge=0)
    max_bots: int = Field(default=1, ge=0)
    max_messages_per_month: int = Field(default=500, ge=0)
    max_intents: int = Field(default=20, ge=0)
    max_commands: int = Field(default=10, ge=0)
    max_memory_items: int = Field(default=100, ge=0)
    has_llm: bool = False
    llm_provider: str = ""
    llm_model: str = ""
    llm_tokens_per_day: int = 0
    has_flora_ai: bool = False
    has_media: bool = False
    has_pdf: bool = False
    has_image: bool = False
    has_audio: bool = False
    has_transcription: bool = False
    has_webhooks: bool = False
    has_api_access: bool = False
    has_analytics: bool = False
    has_white_label: bool = False
    has_campaigns: bool = False
    has_multi_agent: bool = False
    priority_support: bool = False
    is_active: bool = True
    is_public: bool = True
    display_order: int = 0
    features_json: Dict[str, Any] = {}


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_monthly: Optional[float] = Field(None, ge=0)
    price_yearly: Optional[float] = Field(None, ge=0)
    max_bots: Optional[int] = Field(None, ge=0)
    max_messages_per_month: Optional[int] = Field(None, ge=0)
    max_intents: Optional[int] = Field(None, ge=0)
    max_commands: Optional[int] = Field(None, ge=0)
    has_llm: Optional[bool] = None
    llm_tokens_per_day: Optional[int] = None
    has_flora_ai: Optional[bool] = None
    has_media: Optional[bool] = None
    has_webhooks: Optional[bool] = None
    has_api_access: Optional[bool] = None
    has_analytics: Optional[bool] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    display_order: Optional[int] = None


class PlanResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    price_monthly: float
    price_yearly: float
    max_bots: int
    max_messages_per_month: int
    max_intents: int
    max_commands: int
    has_llm: bool
    llm_provider: str
    llm_model: str
    llm_tokens_per_day: int
    has_flora_ai: bool
    has_media: bool
    has_pdf: bool
    has_image: bool
    has_audio: bool
    has_transcription: bool
    has_webhooks: bool
    has_api_access: bool
    has_analytics: bool
    has_white_label: bool
    has_campaigns: bool
    priority_support: bool
    is_active: bool
    is_public: bool
    display_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class PlanComparison(BaseModel):
    plans: List[PlanResponse]
