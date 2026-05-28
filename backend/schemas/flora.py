"""
Flora Platform — Flora AI Schemas
==================================
Pydantic schemas for Flora AI chat, onboarding, and help endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ─── Chat Schemas ──────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Schema for sending a message to Flora AI."""
    message: str = Field(..., min_length=1, max_length=4000, description="User message text")
    session_id: Optional[str] = Field(None, description="Existing session ID (omit to create new)")


class ChatResponse(BaseModel):
    """Schema for Flora AI chat response."""
    response: str = Field(..., description="Flora's response text")
    session_id: str = Field(..., description="Session ID for continuation")
    intent: str = Field("unknown", description="Detected intent tag")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Intent confidence score")
    tools_used: list[str] = Field(default_factory=list, description="Tools invoked during response")
    is_new_session: bool = Field(False, description="Whether this started a new session")
    message_count: int = Field(0, ge=0, description="Total user messages in this session")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")


# ─── Session Schemas ───────────────────────────────────────────────────

class SessionInfoResponse(BaseModel):
    """Schema for Flora session information."""
    session_id: str
    user_id: str
    user_name: str
    user_plan: str
    message_count: int = 0
    total_tokens: int = 0
    is_onboarding: bool = False
    onboarding_step: int = 0
    last_intent: str = ""
    created_at: str
    updated_at: str
    is_expired: bool = False


class SessionHistoryResponse(BaseModel):
    """Schema for session message history."""
    session_id: str
    messages: list[dict[str, Any]]
    message_count: int = 0
    total_tokens: int = 0


class SessionListResponse(BaseModel):
    """Schema for listing Flora sessions."""
    sessions: list[SessionInfoResponse]
    total: int


class SessionDeleteResponse(BaseModel):
    """Schema for session deletion confirmation."""
    success: bool
    message: str
    session_id: str


# ─── Onboarding Schemas ────────────────────────────────────────────────

class OnboardingStepSchema(BaseModel):
    """A single onboarding step."""
    step: int = Field(..., ge=1, le=6)
    title: str
    description: str
    action: str
    emoji: str
    is_completed: bool = False


class OnboardingStateSchema(BaseModel):
    """Current onboarding state for a user."""
    is_onboarding: bool = False
    current_step: int = Field(0, ge=0, le=6)
    completed_steps: list[int] = Field(default_factory=list)
    steps: list[OnboardingStepSchema] = Field(default_factory=list)


class OnboardingStepResponse(BaseModel):
    """Response when requesting a specific onboarding step."""
    step: int
    title: str
    content: str
    emoji: str
    next_hint: Optional[str] = None
    is_last_step: bool = False


class OnboardingProgressRequest(BaseModel):
    """Request to advance onboarding."""
    session_id: str
    action: str = Field("advance", description="Action: 'advance', 'go_to', 'skip'")
    target_step: Optional[int] = Field(None, ge=1, le=6, description="Target step for 'go_to'")


# ─── Help Schemas ──────────────────────────────────────────────────────

class HelpTopicSchema(BaseModel):
    """A help topic with content."""
    topic: str
    title: str
    content: str
    related_topics: list[str] = Field(default_factory=list)


class HelpTopicRequest(BaseModel):
    """Request help for a specific topic."""
    topic: str = Field(..., description="Help topic key")
    question: Optional[str] = Field(None, description="Specific question about the topic")


class HelpTopicListResponse(BaseModel):
    """List of all available help topics."""
    topics: list[dict[str, Any]]


# ─── Suggestion Schemas ────────────────────────────────────────────────

class SuggestionsResponse(BaseModel):
    """Contextual suggestions for the user."""
    suggestions: list[str]
    context: str = ""
