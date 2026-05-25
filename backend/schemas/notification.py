"""Flora Platform — Notification Schemas"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    user_id: str
    title: str = Field(..., max_length=255)
    message: str
    type: str = Field(default="info", pattern="^(info|warning|error|success)$")
    category: str = Field(default="system", pattern="^(system|license|bot|billing)$")
    action_url: str = Field(default="")
    data: dict = Field(default_factory=dict)


class NotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    message: Optional[str] = None
    type: Optional[str] = Field(None, pattern="^(info|warning|error|success)$")
    category: Optional[str] = Field(None, pattern="^(system|license|bot|billing)$")
    is_read: Optional[bool] = None
    action_url: Optional[str] = None
    read_at: Optional[datetime] = None


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str
    category: str
    is_read: bool
    action_url: str
    data: dict
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


class NotificationMarkRead(BaseModel):
    notification_ids: list[str] = Field(default_factory=list)
    mark_all: bool = False
