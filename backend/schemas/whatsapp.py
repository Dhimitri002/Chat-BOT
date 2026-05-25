"""
Flora Platform — WhatsApp Schemas (Pydantic)
=============================================
Request/response schemas for the WhatsApp API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ─── Connection Requests ────────────────────────────────────────────

class ConnectRequest(BaseModel):
    """Request to connect a WhatsApp session."""
    bot_id: str
    session_id: Optional[str] = None
    phone_number: Optional[str] = None
    webhook_url: Optional[str] = None


class DisconnectRequest(BaseModel):
    """Request to disconnect a WhatsApp session."""
    session_id: Optional[str] = None
    bot_id: Optional[str] = None
    remove_data: bool = False  # If True, delete stored auth state


# ─── Connection Responses ───────────────────────────────────────────

class ConnectResponse(BaseModel):
    """Response from a connect request."""
    success: bool
    session_id: str
    state: str
    qr_code: Optional[str] = None  # base64 PNG
    qr_expires_at: Optional[datetime] = None
    message: str


class DisconnectResponse(BaseModel):
    """Response from a disconnect request."""
    success: bool
    session_id: str
    message: str


# ─── Status ─────────────────────────────────────────────────────────

class StatusResponse(BaseModel):
    """Full connection status."""
    session_id: str
    bot_id: Optional[str] = None
    state: str
    phone_number: Optional[str] = None
    push_name: Optional[str] = None
    battery_level: Optional[int] = None
    plugged_in: Optional[bool] = None
    connected_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    retry_count: int = 0
    qr_code: Optional[str] = None  # base64 PNG or "expired"
    is_healthy: bool = False
    is_qr_valid: bool = False
    message: str = ""


class SessionInfo(BaseModel):
    """Brief session information for listing."""
    session_id: str
    bot_id: str = ""
    state: str
    phone_number: Optional[str] = None
    push_name: Optional[str] = None
    connected_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class SessionsResponse(BaseModel):
    """Response listing all sessions."""
    sessions: list[SessionInfo] = Field(default_factory=list)
    total: int = 0


# ─── QR Code ────────────────────────────────────────────────────────

class QrResponse(BaseModel):
    """QR code response."""
    session_id: str
    qr_code: str  # base64 PNG
    qr_string: str  # raw QR string
    expires_at: datetime


class RefreshQrResponse(BaseModel):
    """Refreshed QR code response."""
    session_id: str
    qr_code: str
    qr_string: str
    expires_at: datetime
    message: str


# ─── Message Sending ────────────────────────────────────────────────

class SendMessageRequest(BaseModel):
    """Request to send a WhatsApp message."""
    session_id: str
    to: str = Field(..., description="Phone number in international format, digits only")
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None  # image, video, audio, document
    media_caption: Optional[str] = None
    media_filename: Optional[str] = None
    buttons: Optional[list[dict]] = None
    reply_to: Optional[str] = None  # message ID to reply to

    @field_validator("to")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate and normalize phone number."""
        cleaned = v.strip().replace("+", "").replace("-", "").replace(" ", "")
        if not cleaned.isdigit():
            raise ValueError(f"Invalid phone number: {v}. Use digits only.")
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError(f"Phone number must be 10-15 digits: {v}")
        return cleaned

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("image", "video", "audio", "document"):
            raise ValueError(f"Invalid media_type: {v}. Must be image, video, audio, or document.")
        return v


class SendMessageResponse(BaseModel):
    """Response from sending a message."""
    success: bool
    message_id: Optional[str] = None
    timestamp: datetime
    message: str


# ─── Health Check ───────────────────────────────────────────────────

class HealthCheckResponse(BaseModel):
    """WhatsApp service health check."""
    status: str  # healthy, degraded, unhealthy
    active_sessions: int = 0
    qr_waiting: int = 0
    errors: int = 0
    total_sessions: int = 0
    timestamp: datetime


# ─── Webhook Events (Incoming) ──────────────────────────────────────

class WebhookEvent(BaseModel):
    """Incoming webhook event from the connector."""
    event: str  # message, status, qr, connected, disconnected
    session_id: str
    timestamp: datetime
    data: dict = Field(default_factory=dict)


class WebhookResponse(BaseModel):
    """Response to a webhook event."""
    success: bool
    message: str = "ok"
