"""
Flora Platform — WhatsApp Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class WhatsAppConnect(BaseModel):
    bot_id: str


class WhatsAppDisconnect(BaseModel):
    session_id: str


class WhatsAppSendMessage(BaseModel):
    session_id: str
    to: str = Field(..., description="Phone number with country code, e.g. 5511999999999")
    message: str = Field(..., min_length=1, max_length=4096)
    message_type: str = "text"  # text, image, document


class WhatsAppSendMedia(BaseModel):
    session_id: str
    to: str
    media_url: str
    caption: str = ""
    media_type: str = "image"  # image, audio, video, document


class QRCodeResponse(BaseModel):
    session_id: str
    qr_code: str  # base64 encoded QR
    expires_at: Optional[datetime] = None
    status: str


class SessionStatusResponse(BaseModel):
    session_id: str
    bot_id: str
    status: str
    phone_number: str = ""
    phone_name: str = ""
    connected_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    error_message: str = ""


class SessionListResponse(BaseModel):
    sessions: list[SessionStatusResponse]
    total: int


class WhatsAppWebhook(BaseModel):
    event: str
    session_id: str
    data: Dict[str, Any] = {}
