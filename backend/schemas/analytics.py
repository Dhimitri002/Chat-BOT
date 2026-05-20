"""
Flora Platform — Analytics Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DateRange(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    period_days: int = 30


class BotAnalytics(DateRange):
    bot_id: str


class BotStatsResponse(BaseModel):
    bot_id: str
    period_days: int
    total_messages: int
    inbound_messages: int
    outbound_messages: int
    unique_users: int
    intents_matched: int
    commands_used: int
    llm_tokens_used: int
    llm_cost: float
    avg_response_time_ms: float
    messages_per_day: Dict[str, int] = {}  # date -> count
    top_intents: List[Dict[str, Any]] = []
    top_commands: List[Dict[str, Any]] = []


class AdminDashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_bots: int
    active_bots: int
    total_licenses: int
    active_licenses: int
    expiring_licenses: int
    total_revenue: float
    monthly_revenue: float
    messages_today: int
    messages_this_month: int
    llm_tokens_today: int
    llm_cost_today: float
    new_users_today: int
    new_users_this_month: int
    top_plans: List[Dict[str, Any]] = []
    revenue_by_month: Dict[str, float] = {}


class LLMUsageStats(DateRange):
    user_id: Optional[str] = None
    bot_id: Optional[str] = None


class LLMUsageResponse(BaseModel):
    total_tokens_input: int
    total_tokens_output: int
    total_cost: float
    total_requests: int
    success_rate: float
    avg_latency_ms: float
    usage_by_model: Dict[str, Dict[str, Any]] = {}
    usage_by_day: Dict[str, Dict[str, Any]] = {}
