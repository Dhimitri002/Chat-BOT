"""
Conversation Context Management — Flora Platform
==================================================
Manages conversation state, user data, and message history
for each active session.

Features:
    - Per-session context with user data
    - Message history with configurable limits
    - Session expiry and cleanup
    - Context serialization for persistence
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── Constants ─────────────────────────────────────────────────────────

DEFAULT_MAX_HISTORY = 20
DEFAULT_SESSION_TTL = 3600  # 1 hour in seconds
MAX_CONTEXT_AGE = 86400  # 24 hours max


@dataclass
class MessageRecord:
    """A single message in the conversation history."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MessageRecord:
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            metadata=data.get("metadata", {}),
        )


class ConversationContext:
    """
    Holds the context for a single conversation session.

    Attributes:
        session_id: Unique session identifier
        user_id: User identifier (phone number)
        user_name: User's display name
        user_plan: User's subscription plan
        history: Deque of message records
        metadata: Additional session metadata
        is_onboarding: Whether the user is in onboarding mode
        onboarding_step: Current onboarding step (0-6)
        last_intent: Last detected intent
    """

    def __init__(
        self,
        session_id: str,
        user_id: str = "",
        user_name: str = "",
        user_plan: str = "free",
        max_history: int = DEFAULT_MAX_HISTORY,
        metadata: Optional[dict] = None,
    ):
        self.session_id: str = session_id
        self.user_id: str = user_id
        self.user_name: str = user_name
        self.user_plan: str = user_plan
        self.max_history: int = max_history
        self._history: deque[MessageRecord] = deque(maxlen=max_history)
        self.metadata: dict = metadata or {}
        self.is_onboarding: bool = False
        self.onboarding_step: int = 0
        self.last_intent: str = ""
        self.message_count: int = 0
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.last_activity: str = self.created_at
        self.is_expired: bool = False

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: "user" or "assistant"
            content: Message text
            metadata: Optional metadata (intent, confidence, etc.)
        """
        if role == "user":
            self.message_count += 1

        msg = MessageRecord(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self._history.append(msg)
        self.last_activity = datetime.now(timezone.utc).isoformat()

    def get_history(self) -> list[MessageRecord]:
        """Return the full message history as a list."""
        return list(self._history)

    def get_recent_context(self, n: int = 10) -> list[dict[str, str]]:
        """
        Get the last N messages as dicts for LLM context.

        Args:
            n: Number of recent messages to return

        Returns:
            List of {"role": ..., "content": ...} dicts
        """
        recent = list(self._history)[-n:]
        return [{"role": msg.role, "content": msg.content} for msg in recent]

    def clear(self) -> None:
        """Clear the message history while keeping session data."""
        self._history.clear()
        self.message_count = 0
        self.last_activity = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize context to dictionary for persistence."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_plan": self.user_plan,
            "history": [msg.to_dict() for msg in self._history],
            "metadata": self.metadata,
            "is_onboarding": self.is_onboarding,
            "onboarding_step": self.onboarding_step,
            "last_intent": self.last_intent,
            "message_count": self.message_count,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "max_history": self.max_history,
        }

    def to_json(self) -> str:
        """Serialize context to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> ConversationContext:
        """Deserialize context from dictionary."""
        ctx = cls(
            session_id=data["session_id"],
            user_id=data.get("user_id", ""),
            user_name=data.get("user_name", ""),
            user_plan=data.get("user_plan", "free"),
            max_history=data.get("max_history", DEFAULT_MAX_HISTORY),
            metadata=data.get("metadata", {}),
        )

        # Restore history
        for msg_data in data.get("history", []):
            msg = MessageRecord.from_dict(msg_data)
            ctx._history.append(msg)

        ctx.is_onboarding = data.get("is_onboarding", False)
        ctx.onboarding_step = data.get("onboarding_step", 0)
        ctx.last_intent = data.get("last_intent", "")
        ctx.message_count = data.get("message_count", 0)
        ctx.created_at = data.get("created_at", ctx.created_at)
        ctx.last_activity = data.get("last_activity", ctx.created_at)

        return ctx

    def get_summary(self) -> dict[str, Any]:
        """Return a summary of the current context state."""
        return {
            "session_id": self.session_id,
            "user": self.user_name or self.user_id or "anonymous",
            "plan": self.user_plan,
            "messages": self.message_count,
            "onboarding": self.is_onboarding,
            "step": self.onboarding_step,
            "last_intent": self.last_intent,
            "ttl_remaining": self._get_ttl_remaining(),
        }

    def get_user_preferences(self) -> dict[str, Any]:
        """Extract user preferences from conversation history."""
        preferences = {
            "name": self.user_name,
            "plan": self.user_plan,
            "language": "pt-BR",
            "onboarding_complete": not self.is_onboarding and self.onboarding_step >= 6,
        }

        # Check metadata for preferences
        if "language" in self.metadata:
            preferences["language"] = self.metadata["language"]
        if "emoji_preference" in self.metadata:
            preferences["emoji_preference"] = self.metadata["emoji_preference"]

        return preferences

    def update_user_preference(self, key: str, value: Any) -> None:
        """Update a user preference."""
        self.metadata[key] = value

    def _get_ttl_remaining(self) -> int:
        """Get remaining time-to-live in seconds."""
        last = datetime.fromisoformat(self.last_activity)
        now = datetime.now(timezone.utc)
        elapsed = (now - last).total_seconds()
        return max(0, int(DEFAULT_SESSION_TTL - elapsed))

    def __repr__(self) -> str:
        return (
            f"<ConversationContext(session={self.session_id[:8]}..., "
            f"user={self.user_name or 'anon'}, msgs={self.message_count})>"
        )


class ContextManager:
    """
    Manages multiple conversation contexts (sessions).

    Handles:
    - Session creation and retrieval
    - Session expiry and cleanup
    - In-memory session storage
    """

    def __init__(self, default_ttl: int = DEFAULT_SESSION_TTL):
        self._sessions: dict[str, ConversationContext] = {}
        self.default_ttl = default_ttl
        logger.info("ContextManager initialized (ttl=%ds)", default_ttl)

    def get_or_create(
        self,
        session_id: str,
        user_id: str = "",
        user_name: str = "",
        user_plan: str = "free",
        **kwargs,
    ) -> ConversationContext:
        """
        Get an existing context or create a new one.

        Args:
            session_id: Unique session ID
            user_id: User identifier
            user_name: User display name
            user_plan: User subscription plan
            **kwargs: Additional args for ConversationContext

        Returns:
            Existing or new ConversationContext
        """
        if session_id in self._sessions:
            ctx = self._sessions[session_id]
            ctx.last_activity = datetime.now(timezone.utc).isoformat()
            return ctx

        ctx = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            user_name=user_name,
            user_plan=user_plan,
            **kwargs,
        )
        self._sessions[session_id] = ctx
        logger.debug("Created new context: %s", ctx)
        return ctx

    def get(self, session_id: str) -> Optional[ConversationContext]:
        """
        Get an existing context by session ID.

        Args:
            session_id: Session identifier

        Returns:
            ConversationContext if found and not expired, None otherwise
        """
        ctx = self._sessions.get(session_id)
        if ctx is None:
            return None

        # Check expiry
        if ctx._get_ttl_remaining() <= 0:
            ctx.is_expired = True
            logger.debug("Session expired: %s", session_id[:8])
            return None

        ctx.last_activity = datetime.now(timezone.utc).isoformat()
        return ctx

    def delete(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session to delete

        Returns:
            True if session was found and deleted
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug("Deleted session: %s", session_id[:8])
            return True
        return False

    def clear_history(self, session_id: str) -> bool:
        """Clear message history for a session."""
        ctx = self._sessions.get(session_id)
        if ctx is None:
            return False
        ctx.clear()
        return True

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all active sessions with summaries."""
        return [ctx.to_dict() for ctx in self._sessions.values() if not ctx.is_expired]

    def cleanup_expired(self) -> int:
        """
        Remove expired sessions.

        Returns:
            Number of sessions removed
        """
        expired_keys = [
            sid for sid, ctx in self._sessions.items()
            if ctx._get_ttl_remaining() <= 0
        ]
        for key in expired_keys:
            del self._sessions[key]
            logger.debug("Cleaned up expired session: %s", key[:8])

        if expired_keys:
            logger.info("Cleaned up %d expired sessions", len(expired_keys))
        return len(expired_keys)

    @property
    def active_count(self) -> int:
        """Number of active (non-expired) sessions."""
        return sum(
            1 for ctx in self._sessions.values()
            if ctx._get_ttl_remaining() > 0
        )

    def save_to_file(self, filepath: str) -> None:
        """Save all sessions to a JSON file for persistence."""
        data = {
            sid: ctx.to_dict()
            for sid, ctx in self._sessions.items()
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Saved %d sessions to %s", len(data), filepath)

    def load_from_file(self, filepath: str) -> int:
        """Load sessions from a JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            count = 0
            for sid, ctx_data in data.items():
                ctx = ConversationContext.from_dict(ctx_data)
                # Only load non-expired sessions
                if ctx._get_ttl_remaining() > 0:
                    self._sessions[sid] = ctx
                    count += 1

            logger.info("Loaded %d sessions from %s", count, filepath)
            return count
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to load sessions from %s: %s", filepath, e)
            return 0

    def __repr__(self) -> str:
        return f"<ContextManager(sessions={len(self._sessions)}, active={self.active_count})>"
