"""
Flora Platform — Chat Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    to: str
    message: str
    session_id: str = ""


class SendMessageRequest(BaseModel):
    bot_id: str
    to: str
    content: str
    message_type: str = "text"


class ChatHistoryRequest(BaseModel):
    bot_id: str
    user_phone: Optional[str] = None
    limit: int = 50
    offset: int = 0


class ChatHistoryItem(BaseModel):
    id: str
    direction: str
    content: str
    message_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    items: List[ChatHistoryItem]
    total: int
    page: int
    page_size: int


class ChatConversation(BaseModel):
    bot_id: str
    bot_name: str
    user_phone: str
    last_message: str
    last_message_at: datetime
    message_count: int
    unread_count: int = 0
