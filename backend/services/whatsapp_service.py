"""
Flora Platform — WhatsApp Service
=================================
Full WhatsApp Web connection manager using the Baileys-compatible
remote session approach. Manages QR generation, session persistence,
reconnection with exponential backoff, message sending/receiving,
and connection state tracking.

Architecture:
  WhatsAppService  — singleton per bot session, owns the connection lifecycle
  SessionStore     — persists auth state to disk for reconnection
  MessageDispatcher — routes incoming messages to the Flora engine
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import io
import json
import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import httpx
import qrcode
from qrcode.image.pil import PilImage
from pydantic import BaseModel, Field

from backend.config import settings
from backend.models.whatsapp_event import WhatsAppEvent, EventType

logger = logging.getLogger(__name__)


# ─── Connection State ──────────────────────────────────────────────

class ConnectionState(str, Enum):
    """All possible states for a WhatsApp connection."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    QR_WAITING = "qr_waiting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    LOGGED_OUT = "logged_out"
    ERROR = "error"


# ─── Data Models ────────────────────────────────────────────────────

class WhatsAppConfig(BaseModel):
    """Configuration for a WhatsApp session connection."""
    session_id: str
    bot_id: str
    phone_number: Optional[str] = None
    auth_dir: str = ".wa_sessions"
    max_retries: int = 5
    retry_base_delay: float = 2.0
    retry_max_delay: float = 60.0
    ping_interval: int = 30
    request_timeout: int = 15
    connector_url: str = "http://127.0.0.1:3001"
    webhook_url: Optional[str] = None


class ConnectionStatus(BaseModel):
    """Full status of a WhatsApp connection."""
    session_id: str
    bot_id: str
    state: ConnectionState
    phone_number: Optional[str] = None
    push_name: Optional[str] = None
    battery_level: Optional[int] = None
    plugged_in: Optional[bool] = None
    connected_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    last_qr_update: Optional[datetime] = None
    retry_count: int = 0
    qr_code: Optional[str] = None  # base64 PNG
    qr_string: Optional[str] = None
    error_message: Optional[str] = None
    messages_sent: int = 0
    messages_received: int = 0


class QRCodeData(BaseModel):
    """QR code data for WhatsApp Web authentication."""
    qr_code: str  # base64-encoded PNG
    qr_string: str  # raw QR string
    expires_at: datetime


class OutgoingMessage(BaseModel):
    """A message to send via WhatsApp."""
    to: str
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None  # image, video, audio, document
    media_caption: Optional[str] = None
    media_filename: Optional[str] = None
    buttons: Optional[list[dict]] = None
    reply_to: Optional[str] = None  # message ID to reply to


class IncomingMessage(BaseModel):
    """An incoming WhatsApp message."""
    id: str
    from_number: str  # sender phone number
    to_number: str  # session's own phone number
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    media_caption: Optional[str] = None
    timestamp: datetime
    is_group: bool = False
    group_id: Optional[str] = None
    push_name: Optional[str] = None
    session_id: str
    bot_id: str
    raw: dict = Field(default_factory=dict)


class SendResult(BaseModel):
    """Result of sending a message."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── Exponential Backoff ────────────────────────────────────────────

class ExponentialBackoff:
    """Exponential backoff with jitter for reconnection attempts."""

    def __init__(self, base: float = 2.0, max_delay: float = 60.0):
        self.base = base
        self.max_delay = max_delay
        self._attempt = 0

    def next_delay(self) -> float:
        delay = min(self.base * (2 ** self._attempt), self.max_delay)
        self._attempt += 1
        # Add jitter (+/- 25%)
        import random
        jitter = delay * 0.25 * (2 * random.random() - 1)
        return max(0.5, delay + jitter)

    def reset(self):
        self._attempt = 0

    @property
    def attempt(self) -> int:
        return self._attempt


# ─── Rate Limiter ───────────────────────────────────────────────────

class RateLimiter:
    """
    Per-recipient rate limiter.
    Allows N messages per window per recipient, plus global rate limiting.
    """

    def __init__(
        self,
        max_per_recipient_per_minute: int = 15,
        max_global_per_minute: int = 60,
        max_per_recipient_burst: int = 5,
    ):
        self.max_per_recipient = max_per_recipient_per_minute
        self.max_global = max_global_per_minute
        self.max_burst = max_per_recipient_burst
        self._recipient_timestamps: dict[str, list[float]] = defaultdict(list)
        self._global_timestamps: list[float] = []

    def _cleanup(self, timestamps: list[float], window: float = 60.0):
        now = time.time()
        cutoff = now - window
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)

    async def acquire(self, recipient: str) -> bool:
        """
        Try to acquire permission to send.
        Returns True if allowed, False if rate limited.
        """
        now = time.time()

        # Cleanup old entries
        self._cleanup(self._global_timestamps)
        self._cleanup(self._recipient_timestamps[recipient])

        # Check global rate
        if len(self._global_timestamps) >= self.max_global:
            logger.warning("Global rate limit hit (%d msg/min)", self.max_global)
            return False

        # Check per-recipient rate
        if len(self._recipient_timestamps[recipient]) >= self.max_per_recipient:
            logger.warning(
                "Rate limit hit for recipient %s (%d msg/min)",
                recipient, self.max_per_recipient,
            )
            return False

        # Allow burst (within 5 seconds) up to max_burst
        if self._recipient_timestamps[recipient]:
            recent = sum(
                1 for t in self._recipient_timestamps[recipient]
                if now - t < 5
            )
            if recent >= self.max_burst:
                logger.warning("Burst limit hit for recipient %s", recipient)
                return False

        # Record the send
        self._global_timestamps.append(now)
        self._recipient_timestamps[recipient].append(now)
        return True

    def get_wait_time(self, recipient: str) -> float:
        """Get the seconds to wait before sending to this recipient."""
        self._cleanup(self._recipient_timestamps[recipient])
        if len(self._recipient_timestamps[recipient]) < self.max_per_recipient:
            return 0.0
        # Wait until the oldest message in the window expires
        oldest = self._recipient_timestamps[recipient][0]
        return max(0.0, 60.0 - (time.time() - oldest))


# ─── Connection Log ─────────────────────────────────────────────────

class ConnectionLog:
    """Thread-safe connection event log for debugging."""

    def __init__(self, max_entries: int = 500):
        self._entries: list[dict] = []
        self._max_entries = max_entries
        self._lock = asyncio.Lock()

    async def add(self, event_type: str, message: str, details: Optional[dict] = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "message": message,
            "details": details or {},
        }
        async with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self._max_entries:
                self._entries = self._entries[-self._max_entries:]
        logger.debug("[ConnLog] %s: %s", event_type, message)

    async def get_entries(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
    ) -> list[dict]:
        async with self._lock:
            entries = self._entries[:]
        if event_type:
            entries = [e for e in entries if e["type"] == event_type]
        return entries[-limit:]

    async def clear(self):
        async with self._lock:
            self._entries.clear()


# ─── Session Store ──────────────────────────────────────────────────

class SessionStore:
    """
    Persists WhatsApp auth state to disk so sessions survive restarts.
    Each session gets its own directory with auth files.
    """

    def __init__(self, auth_dir: str):
        self.auth_dir = Path(auth_dir)
        self.auth_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self.auth_dir / session_id

    def session_exists(self, session_id: str) -> bool:
        return self._session_path(session_id).exists()

    def save_auth_state(self, session_id: str, state: dict) -> None:
        """Save authentication state to disk."""
        path = self._session_path(session_id)
        path.mkdir(parents=True, exist_ok=True)
        creds_file = path / "creds.json"
        creds_file.write_text(json.dumps(state, indent=2))
        logger.debug("Auth state saved for session %s", session_id)

    def load_auth_state(self, session_id: str) -> Optional[dict]:
        """Load authentication state from disk."""
        creds_file = self._session_path(session_id) / "creds.json"
        if creds_file.exists():
            try:
                return json.loads(creds_file.read_text())
            except (json.JSONDecodeError, IOError):
                logger.warning("Could not load creds for session %s", session_id)
                return None
        return None

    def save_metadata(self, session_id: str, metadata: dict) -> None:
        """Save session metadata (phone, push_name, etc.)."""
        path = self._session_path(session_id)
        path.mkdir(parents=True, exist_ok=True)
        meta_file = path / "metadata.json"
        existing = {}
        if meta_file.exists():
            try:
                existing = json.loads(meta_file.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        existing.update(metadata)
        meta_file.write_text(json.dumps(existing, indent=2))

    def load_metadata(self, session_id: str) -> Optional[dict]:
        """Load session metadata."""
        meta_file = self._session_path(session_id) / "metadata.json"
        if meta_file.exists():
            try:
                return json.loads(meta_file.read_text())
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def delete_session(self, session_id: str) -> None:
        """Remove all session data."""
        import shutil
        path = self._session_path(session_id)
        if path.exists():
            shutil.rmtree(path)
            logger.info("Session data deleted: %s", session_id)

    def list_sessions(self) -> list[str]:
        """List all stored session IDs."""
        sessions = []
        if self.auth_dir.exists():
            for item in self.auth_dir.iterdir():
                if item.is_dir() and (item / "creds.json").exists():
                    sessions.append(item.name)
        return sessions


# ─── WebSocket Notifier ─────────────────────────────────────────────

class WebSocketNotifier:
    """
    Broadcasts WhatsApp events to connected WebSocket clients.
    Used to push real-time updates to the admin and client apps.
    """

    def __init__(self):
        self._connections: dict[str, list] = defaultdict(list)  # bot_id -> [ws]
        self._global: list = []  # global listeners (admin dashboard)
        self._lock = asyncio.Lock()

    async def register(self, websocket, bot_id: Optional[str] = None):
        async with self._lock:
            if bot_id:
                self._connections[bot_id].append(websocket)
            else:
                self._global.append(websocket)
        logger.debug(
            "WebSocket registered (bot=%s, total_bot=%d, global=%d)",
            bot_id, len(self._connections.get(bot_id, [])), len(self._global),
        )

    async def unregister(self, websocket, bot_id: Optional[str] = None):
        async with self._lock:
            if bot_id and bot_id in self._connections:
                self._connections[bot_id] = [
                    ws for ws in self._connections[bot_id] if ws != websocket
                ]
            self._global = [ws for ws in self._global if ws != websocket]

    async def _safe_send(self, websocket, data: dict) -> bool:
        try:
            await websocket.send_json(data)
            return True
        except Exception:
            return False

    async def broadcast_status(self, bot_id: str, status: ConnectionStatus):
        """Broadcast a connection status update."""
        payload = {
            "type": "connection_status",
            "bot_id": bot_id,
            "data": {
                "session_id": status.session_id,
                "state": status.state.value,
                "phone_number": status.phone_number,
                "push_name": status.push_name,
                "connected_at": status.connected_at.isoformat() if status.connected_at else None,
                "last_seen": status.last_seen.isoformat() if status.last_seen else None,
                "retry_count": status.retry_count,
                "error_message": status.error_message,
                "messages_sent": status.messages_sent,
                "messages_received": status.messages_received,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._broadcast(bot_id, payload)

    async def broadcast_qr(self, bot_id: str, qr_code: str, qr_string: str, expires_at: datetime):
        """Broadcast a new QR code."""
        payload = {
            "type": "qr_code",
            "bot_id": bot_id,
            "data": {
                "qr_code": qr_code,
                "qr_string": qr_string,
                "expires_at": expires_at.isoformat(),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._broadcast(bot_id, payload)

    async def broadcast_message(self, bot_id: str, message_data: dict):
        """Broadcast an incoming/outgoing message."""
        payload = {
            "type": "message",
            "bot_id": bot_id,
            "data": message_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._broadcast(bot_id, payload)

    async def _broadcast(self, bot_id: str, payload: dict):
        """Send to all connections for a bot + global listeners."""
        disconnected = []
        async with self._lock:
            targets = list(self._global)
            targets.extend(self._connections.get(bot_id, []))

        for ws in targets:
            if not await self._safe_send(ws, payload):
                disconnected.append((ws, bot_id))

        # Clean up disconnected clients
        for ws, bid in disconnected:
            await self.unregister(ws, bid)


# ─── WhatsApp Session Connection ────────────────────────────────────

class WhatsAppSessionConnection:
    """
    Manages a single WhatsApp session connection.
    Owns the lifecycle: connect -> receive -> respond -> disconnect.
    """

    def __init__(self, config: WhatsAppConfig):
        self.session_id = config.session_id
        self.bot_id = config.bot_id
        self.config = config
        self.state = ConnectionState.DISCONNECTED
        self._phone_number: Optional[str] = None
        self._push_name: Optional[str] = None
        self._battery_level: Optional[int] = None
        self._plugged_in: Optional[bool] = None
        self._connected_at: Optional[datetime] = None
        self._last_seen: Optional[datetime] = None
        self._last_qr_update: Optional[datetime] = None
        self._qr_string: Optional[str] = None
        self._qr_expires: Optional[datetime] = None
        self._qr_expiry_task: Optional[asyncio.Task] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._reconnect_policy = ExponentialBackoff(
            config.retry_base_delay, config.retry_max_delay
        )
        self._poll_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None
        self._health_check_interval = config.ping_interval
        self._store = SessionStore(config.auth_dir)
        self._rate_limiter = RateLimiter()
        self._log = ConnectionLog()
        self._messages_sent = 0
        self._messages_received = 0
        self._error_message: Optional[str] = None
        self._disconnect_event = asyncio.Event()
        self._state_listeners: list[Callable] = []
        self._lock = asyncio.Lock()

        # Connector URL from config
        self._connector_url = getattr(settings, 'WHATSAPP_CONNECTOR_URL', None) or config.connector_url

    @property
    def status(self) -> ConnectionStatus:
        return ConnectionStatus(
            session_id=self.session_id,
            bot_id=self.bot_id,
            state=self.state,
            phone_number=self._phone_number,
            push_name=self._push_name,
            battery_level=self._battery_level,
            plugged_in=self._plugged_in,
            connected_at=self._connected_at,
            last_seen=self._last_seen,
            last_qr_update=self._last_qr_update,
            retry_count=self._reconnect_policy.attempt,
            qr_code=self._generate_qr_image() if self._qr_string else None,
            qr_string=self._qr_string,
            error_message=self._error_message,
            messages_sent=self._messages_sent,
            messages_received=self._messages_received,
        )

    @property
    def notifier(self) -> Optional[WebSocketNotifier]:
        return self._notifier

    @notifier.setter
    def notifier(self, n: WebSocketNotifier):
        self._notifier = n

    def _generate_qr_image(self) -> Optional[str]:
        """Generate a base64 PNG from the current QR string."""
        if not self._qr_string:
            return None
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(self._qr_string)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
        except Exception as e:
            logger.error("QR image generation failed: %s", e)
            return None

    def update_qr(self, qr_string: str, expires_in: int = 60):
        """Update the current QR code."""
        self._qr_string = qr_string
        self._qr_expires = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        self._last_qr_update = datetime.now(timezone.utc)
        logger.info("QR code updated for session %s (expires in %ds)", self.session_id, expires_in)

    def generate_qr(self) -> QRCodeData:
        """Generate a QR code data model from the current QR string."""
        if not self._qr_string:
            raise ValueError("No QR code available. Start a new connection.")
        if self._qr_expires and datetime.now(timezone.utc) > self._qr_expires:
            raise ValueError("QR code expired. Request a new one.")
        return QRCodeData(
            qr_code=self._generate_qr_image(),
            qr_string=self._qr_string,
            expires_at=self._qr_expires or datetime.now(timezone.utc) + timedelta(seconds=60),
        )

    def add_state_listener(self, callback: Callable):
        self._state_listeners.append(callback)

    async def _set_state(self, new_state: ConnectionState, error_msg: Optional[str] = None):
        old_state = self.state
        self.state = new_state
        self._error_message = error_msg
        if new_state == ConnectionState.CONNECTED:
            self._connected_at = datetime.now(timezone.utc)
            self._last_seen = datetime.now(timezone.utc)
        await self._log.add("state_change", f"{old_state} -> {new_state}")
        # Notify listeners
        for cb in self._state_listeners:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(old_state, new_state)
                else:
                    cb(old_state, new_state)
            except Exception as e:
                logger.error("State listener error: %s", e)

    # ── Connector Communication ─────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client for connector communication."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self._connector_url,
                timeout=httpx.Timeout(self.config.request_timeout),
                headers={"Content-Type": "application/json"},
            )
        return self._http_client

    async def _connector_request(
        self, method: str, path: str, **kwargs
    ) -> Optional[dict]:
        """Make a request to the WhatsApp connector service."""
        client = await self._get_client()
        try:
            response = await client.request(method, path, **kwargs)
            if response.status_code == 200:
                return response.json()
            logger.warning(
                "Connector returned %d for %s %s: %s",
                response.status_code, method, path, response.text[:200],
            )
            return None
        except httpx.ConnectError:
            logger.error("Cannot connect to WhatsApp connector at %s", self._connector_url)
            await self._log.add("error", f"Cannot reach connector at {self._connector_url}")
            return None
        except httpx.TimeoutException:
            logger.error("Timeout connecting to WhatsApp connector")
            await self._log.add("error", "Connector timeout")
            return None
        except Exception as e:
            logger.error("Connector request error: %s", e)
            await self._log.add("error", f"Connector error: {e}")
            return None

    # ── Connection Lifecycle ────────────────────────────────────

    async def connect(self) -> Optional[QRCodeData]:
        """
        Start the WhatsApp connection flow.

        1. Check for existing session -> restore if available
        2. Start a new session -> get QR code
        3. Begin polling for events
        """
        await self._set_state(ConnectionState.CONNECTING)
        await self._log.add("connect", "Starting connection...")

        # Try to restore existing session
        existing_auth = self._store.load_auth_state(self.session_id)
        if existing_auth:
            logger.info("Found existing session for %s, attempting restore...", self.session_id)
            restored = await self._try_restore_session(existing_auth)
            if restored:
                await self._start_polling()
                await self._start_health_check()
                await self._log.add("connect", "Session restored from disk")
                return None

            # Restore failed, start fresh
            logger.info("Session restore failed for %s, starting fresh", self.session_id)
            await self._log.add("connect", "Session restore failed, starting fresh")

        # Start new session through connector
        result = await self._connector_request(
            "POST",
            "/session/start",
            json={
                "sessionId": self.session_id,
                "botId": self.bot_id,
            },
        )

        if not result:
            await self._set_state(ConnectionState.ERROR, "Failed to start session on connector")
            raise ConnectionError("Could not start WhatsApp session on connector. Is the connector running?")

        # The connector either returns a QR code or connects immediately
        if result.get("qr"):
            qr_string = result["qr"]
            expires_in = result.get("expiresIn", 60)
            self.update_qr(qr_string, expires_in)
            await self._set_state(ConnectionState.QR_WAITING)
            await self._log.add("qr", "QR code generated", {"expires_in": expires_in})

            # Schedule QR expiry
            if self._qr_expiry_task:
                self._qr_expiry_task.cancel()
            self._qr_expiry_task = asyncio.create_task(self._handle_qr_expiry(expires_in))

            # Start polling for events (to catch when the QR is scanned)
            await self._start_polling()
            await self._start_health_check()

            return QRCodeData(
                qr_code=self._generate_qr_image(),
                qr_string=qr_string,
                expires_at=self._qr_expires,
            )

        if result.get("connected"):
            await self._set_state(ConnectionState.CONNECTED)
            self._phone_number = result.get("phoneNumber", "")
            self._push_name = result.get("pushName", "")
            await self._start_polling()
            await self._start_health_check()
            await self._log.add("connect", "Connected immediately (no QR needed)", {
                "phone": self._phone_number,
            })
            return None

        await self._set_state(ConnectionState.ERROR, "Unexpected connector response")
        raise ConnectionError("Unexpected response from WhatsApp connector")

    async def _try_restore_session(self, auth_state: dict) -> bool:
        """Try to restore a session using saved auth state."""
        result = await self._connector_request(
            "POST",
            "/session/restore",
            json={
                "sessionId": self.session_id,
                "botId": self.bot_id,
                "state": auth_state,
            },
        )

        if result and result.get("connected"):
            await self._set_state(ConnectionState.CONNECTED)
            self._phone_number = result.get("phoneNumber", "")
            self._push_name = result.get("pushName", "")
            self._reconnect_policy.reset()
            # Load metadata
            meta = self._store.load_metadata(self.session_id) or {}
            if not self._phone_number:
                self._phone_number = meta.get("phone_number")
            if not self._push_name:
                self._push_name = meta.get("push_name")
            return True

        # If restore returns a QR instead
        if result and result.get("qr"):
            qr_string = result["qr"]
            expires_in = result.get("expiresIn", 60)
            self.update_qr(qr_string, expires_in)
            await self._set_state(ConnectionState.QR_WAITING)
            await self._log.add("qr", "New QR after restore attempt", {"expires_in": expires_in})
            return False

        return False

    async def disconnect(self) -> None:
        """Disconnect this session cleanly."""
        logger.info("Disconnecting session %s", self.session_id)
        self._disconnect_event.set()

        # Cancel background tasks
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
            self._health_task = None

        if self._qr_expiry_task:
            self._qr_expiry_task.cancel()
            try:
                await self._qr_expiry_task
            except asyncio.CancelledError:
                pass
            self._qr_expiry_task = None

        # Tell the connector to disconnect
        await self._connector_request(
            "POST",
            "/session/disconnect",
            json={"sessionId": self.session_id},
        )

        # Close the HTTP client
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

        # Cancel any pending connects
        await self._set_state(ConnectionState.DISCONNECTED)
        await self._log.add("disconnect", "Session disconnected")

    async def reconnect(self) -> Optional[QRCodeData]:
        """
        Attempt to reconnect with exponential backoff.
        Returns a new QR code if reconnection requires re-authentication.
        """
        await self._set_state(ConnectionState.RECONNECTING)
        await self._log.add("reconnect", f"Attempt {self._reconnect_policy.attempt + 1}")

        # Close existing client (if any)
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

        delay = self._reconnect_policy.next_delay()
        logger.info("Reconnecting session %s in %.1fs (attempt %d)", self.session_id, delay, self._reconnect_policy.attempt)
        await asyncio.sleep(delay)

        # Check if we got disconnected during the wait
        if self._disconnect_event.is_set():
            return None

        return await self.connect()

    # ── QR Code Expiry ──────────────────────────────────────────

    async def _handle_qr_expiry(self, expires_in: int):
        """Handle QR code expiry."""
        try:
            await asyncio.sleep(expires_in)
            if self.state == ConnectionState.QR_WAITING:
                logger.info("QR code expired for session %s", self.session_id)
                await self._log.add("qr_expired", "QR code expired")
                self._qr_string = None
                self._qr_expires = None
                # Request a new QR from the connector
                result = await self._connector_request(
                    "POST",
                    "/session/qr",
                    json={"sessionId": self.session_id},
                )
                if result and result.get("qr"):
                    qr_string = result["qr"]
                    new_expires = result.get("expiresIn", 60)
                    self.update_qr(qr_string, new_expires)
                    await self._log.add("qr", "Auto-refreshed QR code", {"expires_in": new_expires})
                    # Schedule next expiry
                    self._qr_expiry_task = asyncio.create_task(
                        self._handle_qr_expiry(new_expires)
                    )
                else:
                    await self._log.add("error", "Could not refresh QR code")
        except asyncio.CancelledError:
            pass

    # ── Event Polling ───────────────────────────────────────────

    async def _start_polling(self):
        """Start polling the connector for events."""
        if self._poll_task and not self._poll_task.done():
            return
        self._poll_task = asyncio.create_task(self._poll_events())
        logger.debug("Event polling started for session %s", self.session_id)

    async def _poll_events(self):
        """Poll the connector for new events."""
        logger.info("Event poll loop started for session %s", self.session_id)

        while not self._disconnect_event.is_set():
            try:
                result = await self._connector_request(
                    "GET",
                    f"/session/{self.session_id}/events",
                )

                if result:
                    events = result.get("events", [])
                    for event in events:
                        await self._handle_event(event)

                # Also check connection health
                await self._check_health()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Event polling error: %s", e)
                await self._log.add("error", f"Poll error: {e}")
                await self._handle_connection_error(e)

            await asyncio.sleep(2)  # Poll every 2 seconds

        logger.info("Event polling stopped for session %s", self.session_id)

    async def _handle_event(self, event: dict) -> None:
        """Process a single event from the connector."""
        event_type = event.get("type", "")

        if event_type == "message":
            await self._handle_incoming_message(event)
        elif event_type == "qr":
            qr_string = event.get("qr", "")
            if qr_string:
                self.update_qr(qr_string, event.get("expiresIn", 60))
                if self.state != ConnectionState.QR_WAITING:
                    await self._set_state(ConnectionState.QR_WAITING)
        elif event_type == "connected":
            await self._set_state(ConnectionState.CONNECTED)
            self._phone_number = event.get("phoneNumber", "")
            self._push_name = event.get("pushName", "")
            self._reconnect_policy.reset()
            self._store.save_metadata(self.session_id, {
                "phone_number": self._phone_number,
                "push_name": self._push_name,
                "connected_at": datetime.now(timezone.utc).isoformat(),
            })
            # Clear QR data
            self._qr_string = None
            self._qr_expires = None
            logger.info(
                "Session %s connected as %s (%s)",
                self.session_id, self._phone_number, self._push_name,
            )
            await self._log.add("connected", f"Connected as {self._push_name} ({self._phone_number})")
        elif event_type == "disconnected":
            reason = event.get("reason", "unknown")
            logger.warning("Session %s disconnected: %s", self.session_id, reason)
            await self._log.add("disconnected", f"Disconnected: {reason}", {"reason": reason})
            if reason == "loggedOut":
                await self._set_state(ConnectionState.LOGGED_OUT)
                self._store.delete_session(self.session_id)
            else:
                await self._set_state(ConnectionState.DISCONNECTED)
                # Auto-reconnect for non-logout disconnections
                asyncio.create_task(self._handle_auto_reconnect())
        elif event_type == "connection.update":
            status = event.get("status", "")
            if status == "open":
                await self._set_state(ConnectionState.CONNECTED)
            elif status == "close":
                reason = event.get("reason", "")
                if reason == "loggedOut":
                    await self._set_state(ConnectionState.LOGGED_OUT)
                else:
                    await self._set_state(ConnectionState.DISCONNECTED)
                    asyncio.create_task(self._handle_auto_reconnect())
        elif event_type == "creds.update":
            # Save updated auth state
            state = event.get("state")
            if state:
                self._store.save_auth_state(self.session_id, state)
                await self._log.add("auth", "Auth state updated")
            return
        else:
            logger.debug("Unhandled event type: %s", event_type)
            return

        # Update last_seen
        self._last_seen = datetime.now(timezone.utc)

    async def _handle_auto_reconnect(self):
        """Handle automatic reconnection after unexpected disconnection."""
        if self._disconnect_event.is_set():
            return
        if self._reconnect_policy.attempt >= self.config.max_retries:
            logger.error(
                "Max retries (%d) exceeded for session %s. Giving up.",
                self.config.max_retries, self.session_id,
            )
            await self._set_state(ConnectionState.ERROR, "Max reconnection attempts exceeded")
            await self._log.add("error", "Max reconnection attempts exceeded")
            return

        try:
            qr_data = await self.reconnect()
            # If reconnect returned a QR, the service can broadcast it
            if qr_data and hasattr(self, '_notifier') and self._notifier:
                await self._notifier.broadcast_qr(
                    self.bot_id, qr_data.qr_code, qr_data.qr_string, qr_data.expires_at
                )
        except Exception as e:
            logger.error("Auto-reconnect failed: %s", e)
            await self._set_state(ConnectionState.ERROR, f"Reconnect failed: {e}")

    async def _handle_connection_error(self, error: Exception):
        """Handle a connection error."""
        await self._set_state(ConnectionState.ERROR, str(error))
        logger.error("Connection error for session %s: %s", self.session_id, error)

    # ── Health Monitoring ───────────────────────────────────────

    async def _start_health_check(self):
        """Start periodic health checks."""
        if self._health_task and not self._health_task.done():
            return
        self._health_task = asyncio.create_task(self._health_check_loop())
        logger.debug("Health check started for session %s", self.session_id)

    async def _health_check_loop(self):
        """Periodically check the session health."""
        while not self._disconnect_event.is_set():
            try:
                await asyncio.sleep(self._health_check_interval)
                if self._disconnect_event.is_set():
                    break
                await self._check_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check error: %s", e)

    async def _check_health(self):
        """Check the health of the connection."""
        if self.state not in (ConnectionState.CONNECTED, ConnectionState.QR_WAITING, ConnectionState.CONNECTING):
            return

        result = await self._connector_request("GET", f"/session/{self.session_id}/health")
        if result is None:
            # Connector unreachable
            await self._log.add("health", "Connector unreachable")
            return

        status = result.get("status", "")
        if status == "healthy":
            if self.state != ConnectionState.CONNECTED:
                await self._set_state(ConnectionState.CONNECTED)
            self._last_seen = datetime.now(timezone.utc)
        elif status == "unhealthy":
            await self._log.add("health", f"Unhealthy: {result.get('reason', 'unknown')}")
            await self._handle_connection_error(Exception(f"Health check failed: {result.get('reason')}"))

    # ── Message Handling ────────────────────────────────────────

    async def _handle_incoming_message(self, event: dict) -> None:
        """
        Handle an incoming message event.

        1. Parse the message
        2. Store in database
        3. Store in conversation
        4. Dispatch to Flora engine for AI response
        5. Broadcast via WebSocket
        """
        self._messages_received += 1
        message_id = event.get("id", str(uuid.uuid4()))
        from_number = event.get("from", "")
        is_group = event.get("isGroup", False)

        # Ignore own messages
        if event.get("fromMe", False):
            logger.debug("Ignoring own message %s", message_id)
            return

        # Ignore status/notification messages
        msg_type = event.get("messageType", "")
        if msg_type in ("protocolMessage", "senderKeyDistributionMessage", "messageContextInfo"):
            logger.debug("Ignoring system message type: %s", msg_type)
            return

        logger.info(
            "Incoming message [%s] from %s (group=%s, type=%s)",
            message_id, from_number, is_group, msg_type,
        )
        await self._log.add("message_in", f"From {from_number}", {
            "message_id": message_id,
            "is_group": is_group,
            "text_preview": (event.get("text", "") or "")[:50],
        })

        try:
            text = event.get("text") or event.get("caption") or ""
            # Store message in database
            db_message_id = await self._store_message_in_db(event, text)

            # Store in conversation
            conversation_id = await self._store_in_conversation(event, text)

            # Build incoming message model
            incoming = IncomingMessage(
                id=message_id,
                from_number=from_number,
                to_number=event.get("to", ""),
                text=text if text else None,
                media_url=event.get("mediaUrl"),
                media_type=event.get("mediaType"),
                media_caption=event.get("mediaCaption"),
                timestamp=datetime.fromtimestamp(
                    event.get("timestamp", time.time()), tz=timezone.utc
                ),
                is_group=is_group,
                group_id=event.get("groupId"),
                push_name=event.get("pushName", ""),
                session_id=self.session_id,
                bot_id=self.bot_id,
                raw=event,
            )

            # Dispatch to Flora engine for processing
            try:
                response_text = await self._dispatch_to_flora(incoming)
                if response_text:
                    send_result = await self.send_text(
                        to=from_number,
                        text=response_text,
                        reply_to=message_id if not is_group else None,
                    )
                    if send_result.success:
                        logger.info(
                            "AI response sent to %s (message_id: %s)",
                            from_number, send_result.message_id,
                        )
                    else:
                        logger.warning(
                            "Failed to send AI response to %s: %s",
                            from_number, send_result.error,
                        )
            except Exception as e:
                logger.exception("Error in Flora dispatch for message %s: %s", message_id, e)

        except Exception as e:
            logger.exception("Error handling incoming message: %s", e)
            await self._log.add("error", f"Message handling error: {e}")

    async def _store_message_in_db(self, event: dict, text: str) -> Optional[str]:
        """Store the incoming message in the database."""
        try:
            from backend.database import AsyncSessionLocal
            from backend.models.message import Message
            from sqlalchemy import insert

            message_db_id = str(uuid.uuid4())
            async with AsyncSessionLocal() as db:
                await db.execute(
                    insert(Message).values(
                        id=message_db_id,
                        bot_id=self.bot_id,
                        whatsapp_message_id=event.get("id", ""),
                        direction="in",
                        sender_phone=event.get("from", ""),
                        sender_name=event.get("pushName", ""),
                        message_type=self._map_message_type(event),
                        content=text,
                        media_url=event.get("mediaUrl"),
                        media_type=event.get("mediaType"),
                        media_caption=event.get("mediaCaption"),
                        is_read=False,
                        is_delivered=True,
                        whatsapp_status="received",
                        conversation_id=event.get("conversationId", ""),
                        raw_data=event,
                    )
                )
                await db.commit()
                logger.debug("Message stored in DB: %s", message_db_id)
                return message_db_id
        except Exception as e:
            logger.error("Failed to store message in DB: %s", e)
            return None

    async def _store_in_conversation(self, event: dict, text: str) -> Optional[str]:
        """Store/update the conversation thread."""
        try:
            from backend.database import AsyncSessionLocal
            from backend.models.conversation import Conversation
            from sqlalchemy import select, update

            sender = event.get("from", "")
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Conversation).where(
                        Conversation.bot_id == self.bot_id,
                        Conversation.contact_phone == sender,
                    )
                )
                conversation = result.scalar_one_or_none()

                if conversation:
                    await db.execute(
                        update(Conversation)
                        .where(Conversation.id == conversation.id)
                        .values(
                            last_message=text[:200] if text else "",
                            last_message_at=datetime.now(timezone.utc),
                            unread_count=Conversation.unread_count + 1,
                            updated_at=datetime.now(timezone.utc),
                        )
                    )
                else:
                    db.add(Conversation(
                        id=str(uuid.uuid4()),
                        bot_id=self.bot_id,
                        contact_phone=sender,
                        contact_name=event.get("pushName", ""),
                        last_message=text[:200] if text else "",
                        last_message_at=datetime.now(timezone.utc),
                        unread_count=1,
                    ))
                await db.commit()
                return conversation.id if conversation else None
        except Exception as e:
            logger.error("Failed to update conversation: %s", e)
            return None

    def _map_message_type(self, event: dict) -> str:
        """Map connector message types to internal types."""
        msg_type = event.get("messageType", "")
        type_map = {
            "text": "text",
            "conversation": "text",
            "extendedTextMessage": "text",
            "imageMessage": "image",
            "videoMessage": "video",
            "audioMessage": "audio",
            "documentMessage": "document",
            "documentWithCaptionMessage": "document",
            "stickerMessage": "sticker",
            "locationMessage": "location",
            "contactMessage": "contact",
            "contactsArrayMessage": "contact",
            "buttonsMessage": "buttons",
            "listMessage": "list",
            "templateMessage": "template",
            "reactionMessage": "reaction",
            "pollCreationMessage": "poll",
            "pollUpdateMessage": "poll",
        }
        return type_map.get(msg_type, "text")

    async def _dispatch_to_flora(self, message: IncomingMessage) -> Optional[str]:
        """
        Dispatch an incoming message to the Flora AI engine.
        Returns the response text, or None if no response.
        """
        if not message.bot_id:
            logger.warning("No bot_id on message, cannot dispatch")
            return None

        try:
            from backend.database import AsyncSessionLocal
            from backend.models.bot import Bot
            from sqlalchemy import select

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Bot).where(Bot.id == message.bot_id)
                )
                bot = result.scalar_one_or_none()

                if not bot:
                    logger.warning("Bot %s not found", message.bot_id)
                    return None

                if not bot.is_active:
                    logger.debug("Bot %s inactive, skipping", message.bot_id)
                    return None

                # Check for opted-out users
                if self._is_opted_out(message.from_number):
                    logger.debug("User %s opted out, skipping", message.from_number)
                    return None

                # Process through the chat engine
                from backend.core.chat_engine import ChatEngine
                engine = ChatEngine(db, bot)
                msg_text = message.text or message.media_caption or ""

                response = await engine.process_message(
                    message=msg_text,
                    session_id=message.from_number,
                )

                if response and response.get("content"):
                    return response["content"]
                return None

        except Exception as e:
            logger.exception("Flora dispatch error: %s", e)
            return None

    def _is_opted_out(self, phone: str) -> bool:
        """Check if a user has opted out of bot messages."""
        # Simple file-based opt-out; could be DB in production
        opt_out_file = Path(self.config.auth_dir) / "opt_outs.txt"
        if opt_out_file.exists():
            opts = opt_out_file.read_text().splitlines()
            return phone in opts
        return False

    # ── Message Sending ─────────────────────────────────────────

    async def send_text(
        self,
        to: str,
        text: str,
        reply_to: Optional[str] = None,
    ) -> SendResult:
        """Send a text message."""
        if self.state != ConnectionState.CONNECTED:
            return SendResult(
                success=False,
                error=f"Session is {self.state.value}, not connected",
            )

        # Check rate limit
        if not await self._rate_limiter.acquire(to):
            wait = self._rate_limiter.get_wait_time(to)
            return SendResult(
                success=False,
                error=f"Rate limited. Try again in {wait:.0f}s",
            )

        msg = OutgoingMessage(
            to=to, text=text, reply_to=reply_to
        )
        return await self._send(msg)

    async def send_media(
        self,
        to: str,
        media_url: str,
        media_type: str = "image",
        caption: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> SendResult:
        """Send a media message (image, video, audio, document)."""
        if self.state != ConnectionState.CONNECTED:
            return SendResult(
                success=False,
                error=f"Session is {self.state.value}, not connected",
            )

        if not await self._rate_limiter.acquire(to):
            wait = self._rate_limiter.get_wait_time(to)
            return SendResult(
                success=False,
                error=f"Rate limited. Try again in {wait:.0f}s",
            )

        msg = OutgoingMessage(
            to=to,
            media_url=media_url,
            media_type=media_type,
            media_caption=caption,
            media_filename=filename,
        )
        return await self._send(msg)

    async def send_buttons(
        self,
        to: str,
        text: str,
        buttons: list[dict],
    ) -> SendResult:
        """Send a message with interactive buttons."""
        if self.state != ConnectionState.CONNECTED:
            return SendResult(
                success=False,
                error=f"Session is {self.state.value}, not connected",
            )

        if not await self._rate_limiter.acquire(to):
            return SendResult(
                success=False,
                error="Rate limited",
            )

        msg = OutgoingMessage(
            to=to, text=text, buttons=buttons
        )
        return await self._send(msg)

    async def _send(self, msg: OutgoingMessage) -> SendResult:
        """Send a message through the connector."""
        await self._log.add("message_out", f"To {msg.to}", {
            "type": msg.media_type or "text",
            "text_preview": (msg.text or "")[:50],
        })

        payload = {
            "sessionId": self.session_id,
            "to": self._format_phone(msg.to),
            "text": msg.text,
            "mediaUrl": msg.media_url,
            "mediaType": msg.media_type,
            "caption": msg.media_caption,
            "filename": msg.media_filename,
            "buttons": msg.buttons,
            "replyTo": msg.reply_to,
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        result = await self._connector_request(
            "POST", "/message/send", json=payload
        )

        if result and result.get("messageId"):
            self._messages_sent += 1
            message_id = result["messageId"]
            logger.info("Message sent: %s -> %s (id: %s)", self.session_id, msg.to, message_id)

            # Store outgoing message in DB
            try:
                await self._store_outgoing_in_db(msg, message_id)
            except Exception as e:
                logger.warning("Failed to store outgoing message: %s", e)

            return SendResult(
                success=True,
                message_id=message_id,
            )

        error_msg = result.get("error", "Unknown error") if result else "No response from connector"
        logger.warning("Failed to send message to %s: %s", msg.to, error_msg)
        return SendResult(
            success=False,
            error=error_msg,
        )

    async def _store_outgoing_in_db(self, msg: OutgoingMessage, whatsapp_id: str):
        """Store outgoing message in the database."""
        try:
            from backend.database import AsyncSessionLocal
            from backend.models.message import Message
            from sqlalchemy import insert

            async with AsyncSessionLocal() as db:
                await db.execute(
                    insert(Message).values(
                        id=str(uuid.uuid4()),
                        bot_id=self.bot_id,
                        whatsapp_message_id=whatsapp_id,
                        direction="out",
                        sender_phone=self._phone_number or "",
                        message_type=msg.media_type or "text",
                        content=msg.text or "",
                        media_url=msg.media_url,
                        media_type=msg.media_type,
                        media_caption=msg.media_caption,
                        media_filename=msg.media_filename,
                        is_read=True,
                        is_delivered=False,
                        whatsapp_status="sent",
                        raw_data=msg.model_dump(),
                    )
                )
                await db.commit()
        except Exception as e:
            logger.error("Failed to store outgoing message: %s", e)

    def _format_phone(self, phone: str) -> str:
        """Format a phone number for WhatsApp (digits only, no +)."""
        return phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # ── Logging ─────────────────────────────────────────────────

    async def get_logs(self, limit: int = 100, event_type: Optional[str] = None) -> list[dict]:
        """Get connection logs for debugging."""
        return await self._log.get_entries(limit=limit, event_type=event_type)

    async def clear_logs(self):
        """Clear connection logs."""
        await self._log.clear()


# ─── WhatsApp Service (Singleton Manager) ──────────────────────────

class WhatsAppService:
    """
    Manages all WhatsApp session connections.
    Singleton pattern ensures only one service instance across the app.
    """

    _instance: Optional["WhatsAppService"] = None
    _instance_lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls) -> "WhatsAppService":
        if cls._instance is None:
            async with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
                    # Initialize notifier
                    cls._instance._notifier = WebSocketNotifier()
                    logger.info("WhatsAppService singleton created")
        return cls._instance

    @classmethod
    async def reset_instance(cls):
        """Reset the instance (useful for testing)."""
        if cls._instance:
            for conn in list(cls._instance._sessions.values()):
                await conn.disconnect()
            cls._instance = None

    def __init__(self):
        self._sessions: dict[str, WhatsAppSessionConnection] = {}
        self._bot_session_map: dict[str, str] = {}  # bot_id -> session_id
        self._store = SessionStore(".wa_sessions")
        self._notifier: Optional[WebSocketNotifier] = None
        self._started_at = datetime.now(timezone.utc)
        self._total_messages_sent = 0
        self._total_messages_received = 0
        self._log = ConnectionLog()
        logger.info("WhatsAppService initialized")

    async def create_session(
        self,
        bot_id: str,
        session_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ) -> QRCodeData:
        """
        Create and connect a new WhatsApp session for a bot.

        Returns QRCodeData if a QR code is needed, None if connected immediately.
        """
        sid = session_id or f"bot_{bot_id}"

        # Check if already connected
        existing = self._sessions.get(sid)
        if existing and existing.state == ConnectionState.CONNECTED:
            logger.info("Session %s already connected", sid)
            return None

        # Clean up old session if exists but disconnected
        if existing:
            await existing.disconnect()
            self._sessions.pop(sid, None)
            self._bot_session_map.pop(bot_id, None)

        config = WhatsAppConfig(
            session_id=sid,
            bot_id=bot_id,
            phone_number=phone_number,
            webhook_url=webhook_url,
        )
        conn = WhatsAppSessionConnection(config)
        # Attach the notifier
        if self._notifier:
            conn._notifier = self._notifier
        self._sessions[sid] = conn
        self._bot_session_map[bot_id] = sid

        qr_data = await conn.connect()
        return qr_data

    async def disconnect(self, session_id: str) -> bool:
        """Disconnect a session and clean up."""
        conn = self._sessions.get(session_id)
        if not conn:
            logger.warning("No session found: %s", session_id)
            return False

        await conn.disconnect()
        self._bot_session_map.pop(conn.bot_id, None)
        self._sessions.pop(session_id, None)
        return True

    async def disconnect_bot(self, bot_id: str) -> bool:
        """Disconnect all sessions for a bot."""
        sid = self._bot_session_map.get(bot_id)
        if sid:
            return await self.disconnect(sid)
        return False

    @property
    def status(self) -> Optional[ConnectionStatus]:
        """Get the status of the first active session (for backward compat)."""
        for conn in self._sessions.values():
            return conn.status
        return None

    def get_connection(self, session_id: str) -> Optional[WhatsAppSessionConnection]:
        """Get a connection by session ID."""
        return self._sessions.get(session_id)

    def get_connection_by_bot(self, bot_id: str) -> Optional[WhatsAppSessionConnection]:
        """Get a connection by bot ID."""
        sid = self._bot_session_map.get(bot_id)
        if sid:
            return self._sessions.get(sid)
        return None

    def get_status(self, session_id: str) -> Optional[ConnectionStatus]:
        """Get the status of a session."""
        conn = self._sessions.get(session_id)
        if conn:
            return conn.status
        return None

    def get_status_by_bot(self, bot_id: str) -> Optional[ConnectionStatus]:
        """Get the status of a bot's session."""
        conn = self.get_connection_by_bot(bot_id)
        if conn:
            return conn.status
        return None

    def list_sessions(self) -> list[ConnectionStatus]:
        """List all active sessions."""
        return [conn.status for conn in self._sessions.values()]

    def list_stored_sessions(self) -> list[str]:
        """List all stored session IDs (including disconnected)."""
        return self._store.list_sessions()

    async def send_message(self, session_id: str, message: OutgoingMessage) -> SendResult:
        """Send a message through a specific session."""
        conn = self._sessions.get(session_id)
        if not conn:
            return SendResult(
                success=False,
                error="Session not found",
            )
        result = await conn._send(message)
        if result.success:
            self._total_messages_sent += 1
        return result

    async def send_text(
        self, session_id: str, to: str, text: str, reply_to: Optional[str] = None
    ) -> SendResult:
        """Send a text message through a specific session."""
        conn = self._sessions.get(session_id)
        if not conn:
            return SendResult(
                success=False,
                error="Session not found",
            )
        return await conn.send_text(to, text, reply_to=reply_to)

    async def refresh_qr(self, session_id: str) -> QRCodeData:
        """Request a fresh QR code for a session."""
        conn = self._sessions.get(session_id)
        if not conn:
            raise ValueError("Session not found")
        if conn.state == ConnectionState.CONNECTED:
            raise ValueError("Session is already connected")

        # Request new QR from connector
        result = await conn._connector_request(
            "POST", "/session/qr", json={"sessionId": session_id}
        )
        if not result or not result.get("qr"):
            raise ConnectionError("Connector could not generate a QR code")

        qr_string = result["qr"]
        expires_in = result.get("expiresIn", 60)
        conn.update_qr(qr_string, expires_in)

        # Reschedule expiry
        if conn._qr_expiry_task:
            conn._qr_expiry_task.cancel()
        conn._qr_expiry_task = asyncio.create_task(
            conn._handle_qr_expiry(expires_in)
        )

        return conn.generate_qr()

    async def log_event_to_db(
        self,
        session_id: str,
        event_type: str,
        message: str = "",
        bot_id: str = "",
        phone_number: str = "",
        details: dict | None = None,
    ):
        """Log a WhatsApp event to the database for persistence."""
        try:
            from sqlalchemy.ext.asyncio import AsyncSession
            from backend.database import async_session

            async with async_session() as db:
                event = WhatsAppEvent(
                    session_id=session_id,
                    bot_id=bot_id or "",
                    event_type=event_type,
                    message=message,
                    details=details or {},
                    phone_number=phone_number,
                )
                db.add(event)
                await db.commit()
        except Exception as e:
            logger.error("Failed to log WhatsApp event to DB: %s", e)

    async def process_incoming_webhook(self, payload: dict) -> dict:
        """
        Process an incoming webhook from an external WhatsApp connector/bridge.

        Expected payload format:
        {
            "event": "message" | "qr" | "connected" | "disconnected" | "state_change",
            "session_id": "...",
            "bot_id": "...",
            "data": { ... }
        }

        Returns a dict with status info.
        """
        event_type = payload.get("event", "")
        session_id = payload.get("session_id", "")
        bot_id = payload.get("bot_id", "")
        data = payload.get("data", {})

        logger.info("Webhook received: event=%s session=%s", event_type, session_id)

        # Log the webhook event
        await self.log_event_to_db(
            session_id=session_id,
            event_type=EventType.WEBHOOK_RECEIVED,
            message=f"Webhook: {event_type}",
            bot_id=bot_id,
            details={"event_type": event_type, "data": data},
        )

        conn = self._sessions.get(session_id)

        if event_type == "message" or event_type == "messages.upsert":
            # Incoming message
            from_number = data.get("from", data.get("from_number", ""))
            text = data.get("text", data.get("body", data.get("content", "")))
            push_name = data.get("pushName", data.get("push_name", ""))
            message_id = data.get("id", data.get("message_id", str(uuid.uuid4())))
            media_url = data.get("mediaUrl", data.get("media_url"))
            media_type = data.get("mediaType", data.get("media_type"))
            is_group = data.get("isGroup", data.get("is_group", False))

            # Update stats
            self._total_messages_received += 1

            # Determine the "to" number
            to_number = conn.status.phone_number if conn and conn.status else ""

            # Create a WhatsAppMessage for processing
            msg = WhatsAppMessage(
                id=message_id,
                from_number=from_number,
                to_number=to_number,
                text=text,
                media_url=media_url,
                media_type=media_type,
                push_name=push_name,
                is_group=is_group,
                raw=data,
            )

            # Send to dispatcher if available
            if self._notifier:
                await self._notifier.notify_message(session_id, msg.model_dump())

            # Log the received message event
            await self.log_event_to_db(
                session_id=session_id,
                event_type=EventType.MESSAGE_RECEIVED,
                message=f"Message from {from_number}",
                bot_id=bot_id,
                phone_number=from_number,
                details={"message_id": message_id, "text": text[:200]},
            )

            # Store as outgoing for chat history
            if conn:
                chat_msg = ChatMessage(
                    message_id=message_id,
                    direction="in",
                    sender_phone=from_number,
                    recipient_phone=conn.status.phone_number or "",
                    message_type=media_type or "text",
                    content=text or "",
                    media_url=media_url,
                    timestamp=msg.timestamp,
                    raw=data,
                )
                conn._chat_history.append(chat_msg)
                # Trim history if too large
                if len(conn._chat_history) > conn._max_history:
                    conn._chat_history = conn._chat_history[-conn._max_history:]

            return {"success": True, "message": "Message processed", "message_id": message_id}

        elif event_type == "qr":
            qr_string = data.get("qr", "")
            expires_in = data.get("expiresIn", 60)
            if conn:
                conn.update_qr(qr_string, expires_in)
            await self.log_event_to_db(
                session_id=session_id,
                event_type=EventType.QR_GENERATED,
                message="QR code updated via webhook",
                bot_id=bot_id,
            )
            if self._notifier:
                await self._notifier.notify_qr(session_id, qr_string, expires_in)
            return {"success": True, "message": "QR updated"}

        elif event_type == "connected" or event_type == "connection.open":
            phone = data.get("phoneNumber", data.get("phone_number", ""))
            name = data.get("pushName", data.get("push_name", ""))
            if conn:
                conn._phone = phone
                conn._push_name = name
                conn._state = ConnectionState.CONNECTED
                conn._connected_at = datetime.now(timezone.utc)
                conn._retry_count = 0
            await self.log_event_to_db(
                session_id=session_id,
                event_type=EventType.CONNECTION_ESTABLISHED,
                message=f"Connected: {phone}",
                bot_id=bot_id,
                phone_number=phone,
            )
            if self._notifier:
                await self._notifier.notify_state(
                    session_id, ConnectionState.CONNECTED, phone, name
                )
            return {"success": True, "message": "Connected", "phone": phone}

        elif event_type == "disconnected" or event_type == "connection.close":
            reason = data.get("reason", data.get("message", "unknown"))
            if conn:
                conn._state = ConnectionState.DISCONNECTED
                conn._qr_string = None
            await self.log_event_to_db(
                session_id=session_id,
                event_type=EventType.CONNECTION_LOST,
                message=f"Disconnected: {reason}",
                bot_id=bot_id,
            )
            if self._notifier:
                await self._notifier.notify_state(session_id, ConnectionState.DISCONNECTED)
            return {"success": True, "message": f"Disconnected: {reason}"}

        elif event_type == "state_change":
            new_state = data.get("state", "disconnected")
            state_map = {
                "disconnected": ConnectionState.DISCONNECTED,
                "connecting": ConnectionState.CONNECTING,
                "qr_waiting": ConnectionState.QR_WAITING,
                "qr_ready": ConnectionState.QR_WAITING,
                "connected": ConnectionState.CONNECTED,
                "reconnecting": ConnectionState.RECONNECTING,
                "logged_out": ConnectionState.LOGGED_OUT,
                "error": ConnectionState.ERROR,
            }
            mapped = state_map.get(new_state, ConnectionState.DISCONNECTED)
            if conn:
                conn._state = mapped
            if self._notifier:
                await self._notifier.notify_state(session_id, mapped)
            return {"success": True, "message": f"State: {new_state}"}

        else:
            logger.warning("Unknown webhook event type: %s", event_type)
            await self.log_event_to_db(
                session_id=session_id,
                event_type=EventType.WEBHOOK_ERROR,
                message=f"Unknown event: {event_type}",
                bot_id=bot_id,
            )
            return {"success": False, "message": f"Unknown event type: {event_type}"}

    async def get_chat_history(
        self,
        session_id: str,
        contact_phone: str = "",
        limit: int = 50,
        before_id: str = "",
    ) -> list[ChatMessage]:
        """
        Get the chat history for a session.
        If contact_phone is given, filters to that contact only.
        """
        conn = self._sessions.get(session_id)
        if not conn:
            return []

        messages = conn._chat_history
        if contact_phone:
            normalized = contact_phone.replace("+", "").replace(" ", "")
            messages = [
                m for m in messages
                if m.sender_phone.replace("+", "").replace(" ", "") == normalized
                or m.recipient_phone.replace("+", "").replace(" ", "") == normalized
            ]

        if before_id:
            idx = next((i for i, m in enumerate(messages) if m.message_id == before_id), -1)
            if idx > 0:
                messages = messages[:idx]

        return messages[-limit:] if len(messages) > limit else messages

    async def get_events_from_db(
        self,
        session_id: str,
        limit: int = 100,
        event_type: str = "",
    ) -> list[dict]:
        """Get WhatsApp events from the database."""
        try:
            from backend.database import async_session

            async with async_session() as db:
                from sqlalchemy import select, desc

                stmt = select(WhatsAppEvent).where(WhatsAppEvent.session_id == session_id)

                if event_type:
                    stmt = stmt.where(WhatsAppEvent.event_type == event_type)

                stmt = stmt.order_by(desc(WhatsAppEvent.created_at)).limit(limit)
                result = await db.execute(stmt)
                events = result.scalars().all()

                return [
                    {
                        "id": e.id,
                        "event_type": e.event_type,
                        "message": e.message,
                        "details": e.details,
                        "phone_number": e.phone_number,
                        "created_at": e.created_at.isoformat(),
                    }
                    for e in events
                ]
        except Exception as e:
            logger.error("Failed to get events from DB: %s", e)
            return []

    async def get_session_logs(
        self, session_id: str, limit: int = 100, event_type: Optional[str] = None
    ) -> list[dict]:
        """Get logs for a specific session (in-memory + DB)."""
        conn = self._sessions.get(session_id)
        if not conn:
            return []
        return await conn.get_logs(limit=limit, event_type=event_type)

    async def get_service_stats(self) -> dict:
        """Get overall service statistics."""
        active = sum(
            1 for c in self._sessions.values()
            if c.state == ConnectionState.CONNECTED
        )
        return {
            "total_sessions": len(self._sessions),
            "active_sessions": active,
            "total_messages_sent": self._total_messages_sent,
            "total_messages_received": self._total_messages_received,
            "uptime_seconds": (datetime.now(timezone.utc) - self._started_at).total_seconds(),
            "stored_sessions": len(self._store.list_sessions()),
        }
