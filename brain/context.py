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
        message_count: Total messages in this session
        created_at: Session creation timestamp
        last_activity: Last message timestamp
        is_onboarding: Whether user is in onboarding flow
        onboarding_step: Current onboarding step (1-6)
        metadata: Additional session metadata
    """

    def __init__(
        self,
        session_id: str,
        user_id: str = "",
        user_name: str = "",
        user_plan: str = "free",
        max_history: int = DEFAULT_MAX_HISTORY,
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.user_name = user_name
        self.user_plan = user_plan
        self.max_history = max_history

        # Timestamps
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.last_activity: str = self.created_at

        # State
        self.message_count: int = 0
        self.is_onboarding: bool = False
        self.onboarding_step: int = 0
        self.last_intent: str = ""

        # Message history (bounded deque)
        self._history: deque[MessageRecord] = deque(maxlen=max_history)

        # Arbitrary metadata
        self.metadata: dict[str, Any] = {}

    @property
    def history(self) -> list[MessageRecord]:
        """Get message history as a list."""
        return list(self._history)

    @property
    def is_expired(self) -> bool:
        """Check if the session has expired based on TTL."""
        try:
            last = datetime.fromisoformat(self.last_activity)
            now = datetime.now(timezone.utc)
            age = (now - last).total_seconds()
            return age > DEFAULT_SESSION_TTL
        except (ValueError, TypeError):
            return False

    @property
    def age_seconds(self) -> float:
        """Get session age in seconds."""
        try:
            created = datetime.fromisoformat(self.created_at)
            now = datetime.now(timezone.utc)
            return (now - created).total_seconds()
        except (ValueError, TypeError):
            return 0.0

    def add_message(self, role: str, content: str, metadata: Optional[dict] = None) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: "user" or "assistant"
            content: Message text
            metadata: Optional metadata dict
        """
        record = MessageRecord(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self._history.append(record)
        self.message_count += 1
        self.last_activity = datetime.now(timezone.utc).isoformat()

    def get_last_user_message(self) -> Optional[str]:
        """Get the last message from the user."""
        for msg in reversed(self._history):
            if msg.role == "user":
                return msg.content
        return None

    def get_last_assistant_message(self) -> Optional[str]:
        """Get the last message from the assistant."""
        for msg in reversed(self._history):
            if msg.role == "assistant":
                return msg.content
        return None

    def get_recent_context(self, n: int = 5) -> list[dict]:
        """
        Get the last n messages as dicts (for LLM context).

        Args:
            n: Number of recent messages to return

        Returns:
            List of {"role": str, "content": str} dicts
        """
        recent = list(self._history)[-n:]
        return [{"role": m.role, "content": m.content} for m in recent]

    def start_onboarding(self) -> None:
        """Mark the session as in onboarding."""
        self.is_onboarding = True
        self.onboarding_step = 1
        self.metadata["onboarding_started"] = datetime.now(timezone.utc).isoformat()

    def advance_onboarding(self) -> bool:
        """
        Advance to the next onboarding step.

        Returns:
            True if there are more steps, False if onboarding is complete
        """
        self.onboarding_step += 1
        if self.onboarding_step > 6:
            self.is_onboarding = False
            self.metadata["onboarding_completed"] = datetime.now(timezone.utc).isoformat()
            return False
        return True

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value."""
        return self.metadata.get(key, default)

    def to_dict(self) -> dict:
        """Serialize context to dict."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_plan": self.user_plan,
            "message_count": self.message_count,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "is_onboarding": self.is_onboarding,
            "onboarding_step": self.onboarding_step,
            "last_intent": self.last_intent,
            "history": [m.to_dict() for m in self._history],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ConversationContext:
        """Deserialize context from dict."""
        ctx = cls(
            session_id=data["session_id"],
            user_id=data.get("user_id", ""),
            user_name=data.get("user_name", ""),
            user_plan=data.get("user_plan", "free"),
        )
        ctx.message_count = data.get("message_count", 0)
        ctx.created_at = data.get("created_at", ctx.created_at)
        ctx.last_activity = data.get("last_activity", ctx.last_activity)
        ctx.is_onboarding = data.get("is_onboarding", False)
        ctx.onboarding_step = data.get("onboarding_step", 0)
        ctx.last_intent = data.get("last_intent", "")
        ctx.metadata = data.get("metadata", {})

        for msg_data in data.get("history", []):
            record = MessageRecord.from_dict(msg_data)
            ctx._history.append(record)

        return ctx

    def __repr__(self) -> str:
        return (
            f"ConversationContext(session={self.session_id}, "
            f"user={self.user_name or self.user_id}, "
            f"messages={self.message_count}, "
            f"onboarding={'step ' + str(self.onboarding_step) if self.is_onboarding else 'no'})"
        )


class ContextManager:
    """
    Manages multiple conversation contexts.

    Handles creation, retrieval, expiry, and cleanup of sessions.

    Usage:
        manager = ContextManager()
        ctx = manager.get_or_create("session_123", user_id="5511999999999")
        ctx.add_message("user", "Oi!")
        manager.cleanup_expired()
    """

    def __init__(self, max_sessions: int = 10000, default_ttl: int = DEFAULT_SESSION_TTL):
        self._sessions: dict[str, ConversationContext] = {}
        self._max_sessions = max_sessions
        self._default_ttl = default_ttl
        self._total_created = 0
        logger.info("ContextManager initialized", extra={"max_sessions": max_sessions})

    @property
    def active_sessions(self) -> int:
        """Number of active sessions."""
        return len(self._sessions)

    @property
    def total_created(self) -> int:
        """Total sessions created since start."""
        return self._total_created

    def get(self, session_id: str) -> Optional[ConversationContext]:
        """
        Get an existing context by session ID.

        Args:
            session_id: Session identifier

        Returns:
            ConversationContext or None if not found/expired
        """
        ctx = self._sessions.get(session_id)
        if ctx is None:
            return None

        if ctx.is_expired:
            logger.debug(f"Session {session_id} expired, removing")
            del self._sessions[session_id]
            return None

        return ctx

    def get_or_create(
        self,
        session_id: str,
        user_id: str = "",
        user_name: str = "",
        user_plan: str = "free",
    ) -> ConversationContext:
        """
        Get an existing context or create a new one.

        Args:
            session_id: Session identifier
            user_id: User identifier
            user_name: User's display name
            user_plan: User's subscription plan

        Returns:
            ConversationContext (existing or new)
        """
        existing = self.get(session_id)
        if existing:
            # Update user info if provided
            if user_name and not existing.user_name:
                existing.user_name = user_name
            if user_id and not existing.user_id:
                existing.user_id = user_id
            return existing

        # Enforce max sessions limit
        if len(self._sessions) >= self._max_sessions:
            self._evict_oldest()

        ctx = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            user_name=user_name,
            user_plan=user_plan,
        )
        self._sessions[session_id] = ctx
        self._total_created += 1
        logger.debug(f"Created new context: {session_id}")
        return ctx

    def delete(self, session_id: str) -> bool:
        """
        Delete a session.

        Returns:
            True if the session existed and was deleted
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug(f"Deleted context: {session_id}")
            return True
        return False

    def cleanup_expired(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions removed
        """
        expired = [
            sid for sid, ctx in self._sessions.items()
            if ctx.is_expired
        ]
        for sid in expired:
            del self._sessions[sid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        return len(expired)

    def _evict_oldest(self) -> None:
        """Evict the oldest session when at capacity."""
        if not self._sessions:
            return

        oldest_sid = min(
            self._sessions,
            key=lambda sid: self._sessions[sid].last_activity,
        )
        del self._sessions[oldest_sid]
        logger.debug(f"Evicted oldest session: {oldest_sid}")

    def get_stats(self) -> dict:
        """Get manager statistics."""
        return {
            "active_sessions": len(self._sessions),
            "total_created": self._total_created,
            "max_sessions": self._max_sessions,
            "default_ttl": self._default_ttl,
        }

    def save_to_file(self, filepath: str) -> None:
        """Persist all contexts to a JSON file."""
        data = {
            sid: ctx.to_dict()
            for sid, ctx in self._sessions.items()
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} contexts to {filepath}")

    def load_from_file(self, filepath: str) -> int:
        """Load contexts from a JSON file. Returns count loaded."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            count = 0
            for sid, ctx_data in data.items():
                ctx = ConversationContext.from_dict(ctx_data)
                if not ctx.is_expired:
                    self._sessions[sid] = ctx
                    count += 1

            logger.info(f"Loaded {count} contexts from {filepath}")
            return count
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load contexts: {e}")
            return 0
