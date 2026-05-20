"""
Flora Platform — Subscription Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SubscriptionCreate(BaseModel):
    plan_id: str
    billing_cycle: str = "monthly"  # monthly, yearly
    payment_method: str = "credit_card"
    payment_provider: str = "stripe"
    auto_renew: bool = True


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[str] = None
    auto_renew: Optional[bool] = None
    payment_method: Optional[str] = None


class SubscriptionCancel(BaseModel):
    reason: str = ""
    immediate: bool = False


class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan_id: str
    license_id: Optional[str]
    status: str
    billing_cycle: str
    price_paid: float
    currency: str
    started_at: datetime
    expires_at: Optional[datetime]
    canceled_at: Optional[datetime]
    auto_renew: bool
    payment_method: str
    payment_provider: str
    next_payment_at: Optional[datetime]
    grace_period_end: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionWithPlan(SubscriptionResponse):
    plan_name: str = ""
    plan_slug: str = ""
