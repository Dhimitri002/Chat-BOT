"""
Flora Platform — WhatsApp Manager
===================================
Manages WhatsApp sessions, connection states,
and message routing via the whatsapp-web.js or baileys bridge.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class WhatsAppConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    QR_WAITING = "qr_waiting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class MessageDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


@dataclass
class WhatsAppSession:
    """Represents a WhatsApp session."""
    session_id: str
    bot_id: str
    user_id: str
    phone_number: str = ""
    state: WhatsAppConnectionState = WhatsAppConnectionState.DISCONNECTED
    qr_code: str = ""
    qr_timestamp: float = 0.0
    connected_at: Optional[str] = None
    last_seen: Optional[str] = None
    message_count: int = 0
    error_count: int = 0
    session_data: dict = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class WhatsAppMessage:
    """Represents a WhatsApp message."""
    message_id: str
    session_id: str
    direction: MessageDirection
    sender: str = ""
    recipient: str = ""
    content: str = ""
    message_type: str = "text"  # text, image, audio, video, document, location
    media_url: str = ""
    timestamp: str = ""
    is_group: bool = False
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class WhatsAppSessionManager:
    """
    Manages WhatsApp sessions for the Flora Platform.

    Handles:
    - Session lifecycle (connect, disconnect, reconnect)
    - QR code generation and management
    - Message routing to chat engine
    - Multi-session support (one per bot)
    - Session persistence and recovery
    """

    def __init__(
        self,
        sessions_path: str = "data/whatsapp_sessions",
        max_sessions: int = 100,
        qr_timeout_seconds: int = 120,
        auto_reconnect: bool = True,
        reconnect_delay_seconds: int = 5,
    ):
        self._sessions: dict[str, WhatsAppSession] = {}
        self._sessions_path = sessions_path
        self._max_sessions = max_sessions
        self._qr_timeout = qr_timeout_seconds
        self._auto_reconnect = auto_reconnect
        self._reconnect_delay = reconnect_delay_seconds
        self._message_handlers: list[Callable] = []
        self._state_handlers: list[Callable] = []

        os.makedirs(sessions_path, exist_ok=True)
        logger.info(f"WhatsAppSessionManager initialized (max_sessions={max_sessions})")

    # ─── Session Lifecycle ────────────────────────────────────────

    async def create_session(
        self,
        bot_id: str,
        user_id: str,
        phone_number: str = "",
    ) -> WhatsAppSession:
        """Create a new WhatsApp session."""
        session_id = f"wa_{bot_id}"

        if len(self._sessions) >= self._max_sessions:
            # Remove oldest disconnected session
            self._cleanup_disconnected()

        session = WhatsAppSession(
            session_id=session_id,
            bot_id=bot_id,
            user_id=user_id,
            phone_number=phone_number,
        )

        self._sessions[session_id] = session
        logger.info(f"Session created: {session_id} for bot={bot_id}")
        return session

    async def connect(self, session_id: str) -> WhatsAppSession:
        """
        Initiate WhatsApp connection.

        In production, this would start the Baileys/whatsapp-web.js
        connection and wait for QR scan.
        """
        session = self._sessions.get(session_id)
        if not session:
            raise WhatsAppError(f"Session not found: {session_id}")

        session.state = WhatsAppConnectionState.CONNECTING
        session.qr_code = ""
        session.error_count = 0

        logger.info(f"Connecting session: {session_id}")
        await self._notify_state_change(session)

        # In production: start the actual WhatsApp connection here
        # For now, simulate QR code generation
        session.state = WhatsAppConnectionState.QR_WAITING
        session.qr_timestamp = time.time()

        return session

    async def disconnect(self, session_id: str) -> None:
        """Disconnect a WhatsApp session."""
        session = self._sessions.get(session_id)
        if not session:
            return

        session.state = WhatsAppConnectionState.DISCONNECTED
        session.qr_code = ""
        session.connected_at = None

        logger.info(f"Session disconnected: {session_id}")
        await self._notify_state_change(session)

    async def reconnect(self, session_id: str) -> WhatsAppSession:
        """Reconnect a session."""
        session = self._sessions.get(session_id)
        if not session:
            raise WhatsAppError(f"Session not found: {session_id}")

        session.state = WhatsAppConnectionState.RECONNECTING
        session.error_count += 1

        logger.info(f"Reconnecting session: {session_id} (attempt {session.error_count})")
        await self._notify_state_change(session)

        # In production: attempt to restore session from stored credentials
        if self._auto_reconnect and session.error_count < 5:
            await self.connect(session_id)
        else:
            session.state = WhatsAppConnectionState.ERROR
            logger.error(f"Session reconnection failed: {session_id}")

        return session

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its data."""
        session = self._sessions.pop(session_id, None)
        if not session:
            return False

        # Remove session files
        session_file = os.path.join(self._sessions_path, f"{session_id}.json")
        if os.path.exists(session_file):
            os.remove(session_file)

        logger.info(f"Session deleted: {session_id}")
        return True

    # ─── QR Code Management ───────────────────────────────────────

    def get_qr_code(self, session_id: str) -> Optional[str]:
        """Get the current QR code for a session."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        if session.state != WhatsAppConnectionState.QR_WAITING:
            return None

        # Check QR timeout
        if time.time() - session.qr_timestamp > self._qr_timeout:
            logger.warning(f"QR code expired for session: {session_id}")
            return None

        return session.qr_code

    def is_qr_expired(self, session_id: str) -> bool:
        """Check if the QR code has expired."""
        session = self._sessions.get(session_id)
        if not session:
            return True
        return time.time() - session.qr_timestamp > self._qr_timeout

    # ─── Message Handling ─────────────────────────────────────────

    async def send_message(
        self,
        session_id: str,
        to: str,
        content: str,
        message_type: str = "text",
    ) -> WhatsAppMessage:
        """Send a WhatsApp message."""
        session = self._sessions.get(session_id)
        if not session:
            raise WhatsAppError(f"Session not found: {session_id}")

        if session.state != WhatsAppConnectionState.CONNECTED:
            raise WhatsAppError(f"Session not connected: {session_id}")

        import uuid
        message = WhatsAppMessage(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            direction=MessageDirection.OUTGOING,
            recipient=to,
            content=content,
            message_type=message_type,
        )

        # In production: send via Baileys/whatsapp-web.js
        session.message_count += 1
        session.last_seen = datetime.now(timezone.utc).isoformat()

        logger.debug(f"Message sent: {message.message_id} to={to}")
        return message

    async def handle_incoming_message(self, message: WhatsAppMessage) -> None:
        """Process an incoming WhatsApp message."""
        session = self._sessions.get(message.session_id)
        if not session:
            logger.warning(f"Incoming message for unknown session: {message.session_id}")
            return

        session.message_count += 1
        session.last_seen = datetime.now(timezone.utc).isoformat()

        logger.info(
            f"Incoming message: session={message.session_id} "
            f"from={message.sender} type={message.message_type}"
        )

        # Notify registered handlers
        for handler in self._message_handlers:
            try:
                await handler(message, session)
            except Exception as e:
                logger.error(f"Message handler error: {e}", exc_info=True)

    def register_message_handler(self, handler: Callable) -> None:
        """Register a handler for incoming messages."""
        self._message_handlers.append(handler)
        logger.debug(f"Message handler registered: {handler.__name__}")

    def unregister_message_handler(self, handler: Callable) -> None:
        """Remove a message handler."""
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)

    def register_state_handler(self, handler: Callable) -> None:
        """Register a handler for connection state changes."""
        self._state_handlers.append(handler)

    async def _notify_state_change(self, session: WhatsAppSession) -> None:
        """Notify state change handlers."""
        for handler in self._state_handlers:
            try:
                await handler(session)
            except Exception as e:
                logger.error(f"State handler error: {e}", exc_info=True)

    # ─── Session Persistence ──────────────────────────────────────

    async def save_session(self, session_id: str) -> None:
        """Save session data to disk."""
        session = self._sessions.get(session_id)
        if not session:
            return

        filepath = os.path.join(self._sessions_path, f"{session_id}.json")
        data = {
            "session_id": session.session_id,
            "bot_id": session.bot_id,
            "user_id": session.user_id,
            "phone_number": session.phone_number,
            "state": session.state.value,
            "connected_at": session.connected_at,
            "last_seen": session.last_seen,
            "message_count": session.message_count,
            "error_count": session.error_count,
            "session_data": session.session_data,
            "created_at": session.created_at,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, default=str, indent=2)

    async def load_session(self, session_id: str) -> Optional[WhatsAppSession]:
        """Load session data from disk."""
        filepath = os.path.join(self._sessions_path, f"{session_id}.json")
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            session = WhatsAppSession(
                session_id=data["session_id"],
                bot_id=data["bot_id"],
                user_id=data["user_id"],
                phone_number=data.get("phone_number", ""),
                state=WhatsAppConnectionState(data.get("state", "disconnected")),
                connected_at=data.get("connected_at"),
                last_seen=data.get("last_seen"),
                message_count=data.get("message_count", 0),
                error_count=data.get("error_count", 0),
                session_data=data.get("session_data", {}),
                created_at=data.get("created_at", ""),
            )

            self._sessions[session_id] = session
            return session
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    # ─── Query ────────────────────────────────────────────────────

    def get_session(self, session_id: str) -> Optional[WhatsAppSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_session_by_bot(self, bot_id: str) -> Optional[WhatsAppSession]:
        """Get a session by bot ID."""
        for session in self._sessions.values():
            if session.bot_id == bot_id:
                return session
        return None

    def get_sessions_by_user(self, user_id: str) -> list[WhatsAppSession]:
        """Get all sessions for a user."""
        return [s for s in self._sessions.values() if s.user_id == user_id]

    def get_all_sessions(self) -> list[WhatsAppSession]:
        """Get all sessions."""
        return list(self._sessions.values())

    def get_connected_sessions(self) -> list[WhatsAppSession]:
        """Get all connected sessions."""
        return [
            s for s in self._sessions.values()
            if s.state == WhatsAppConnectionState.CONNECTED
        ]

    def get_stats(self) -> dict:
        """Return manager statistics."""
        states = {}
        for s in self._sessions.values():
            state = s.state.value
            states[state] = states.get(state, 0) + 1

        return {
            "total_sessions": len(self._sessions),
            "connected": len(self.get_connected_sessions()),
            "states": states,
            "total_messages": sum(s.message_count for s in self._sessions.values()),
        }

    # ─── Cleanup ──────────────────────────────────────────────────

    def _cleanup_disconnected(self) -> None:
        """Remove disconnected sessions to free capacity."""
        disconnected = [
            sid for sid, s in self._sessions.items()
            if s.state == WhatsAppConnectionState.DISCONNECTED
        ]
        for sid in disconnected[:5]:  # Remove up to 5
            del self._sessions[sid]
            logger.debug(f"Cleaned up disconnected session: {sid}")


class WhatsAppError(Exception):
    """WhatsApp-related error."""
    pass
