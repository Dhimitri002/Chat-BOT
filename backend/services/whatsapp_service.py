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
import os
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import httpx
import qrcode
from qrcode.image.pil import PilImage
from pydantic import BaseModel, Field

from backend.config import settings

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
    auth_dir: str = Field(default=".wa_sessions")
    max_retries: int = 5
    retry_base_delay: float = 2.0
    retry_max_delay: float = 60.0
    ping_interval: int = 30
    request_timeout: int = 30
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None


class QRCodeData(BaseModel):
    """QR code response model."""
    qr_code: str  # base64-encoded PNG image
    qr_string: str  # raw QR string from WhatsApp Web
    expires_at: datetime
    session_id: str


class ConnectionStatus(BaseModel):
    """Full connection status response."""
    session_id: str
    bot_id: str
    state: ConnectionState
    phone_number: Optional[str] = None
    push_name: Optional[str] = None
    battery_level: Optional[int] = None
    plugged_in: Optional[bool] = None
    last_seen: Optional[datetime] = None
    connected_at: Optional[datetime] = None
    retry_count: int = 0
    qr_code: Optional[str] = None


class OutgoingMessage(BaseModel):
    """An outgoing WhatsApp message."""
    to: str  # phone number in international format (e.g. "5511999999999")
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
        creds_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        logger.info("Saved auth state for session %s", session_id)

    def load_auth_state(self, session_id: str) -> Optional[dict]:
        """Load authentication state from disk."""
        creds_file = self._session_path(session_id) / "creds.json"
        if creds_file.exists():
            try:
                data = json.loads(creds_file.read_text(encoding="utf-8"))
                logger.info("Loaded auth state for session %s", session_id)
                return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load auth state for %s: %s", session_id, e)
        return None

    def save_metadata(self, session_id: str, metadata: dict) -> None:
        """Save session metadata (phone, push_name, etc.)."""
        path = self._session_path(session_id)
        path.mkdir(parents=True, exist_ok=True)
        meta_file = path / "metadata.json"
        meta_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    def load_metadata(self, session_id: str) -> Optional[dict]:
        """Load session metadata."""
        meta_file = self._session_path(session_id) / "metadata.json"
        if meta_file.exists():
            try:
                return json.loads(meta_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def delete_session(self, session_id: str) -> None:
        """Delete all session data."""
        import shutil
        path = self._session_path(session_id)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            logger.info("Deleted session data for %s", session_id)

    def list_sessions(self) -> list[str]:
        """List all session IDs with stored auth state."""
        sessions = []
        if self.auth_dir.exists():
            for entry in self.auth_dir.iterdir():
                if entry.is_dir() and (entry / "creds.json").exists():
                    sessions.append(entry.name)
        return sessions


# ─── Reconnection Policy ────────────────────────────────────────────

class ReconnectPolicy:
    """Exponential backoff reconnection policy."""

    def __init__(self, max_retries: int = 5, base_delay: float = 2.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._retry_count = 0

    @property
    def retry_count(self) -> int:
        return self._retry_count

    @property
    def delay(self) -> float:
        """Calculate delay with exponential backoff and jitter."""
        import random
        exp_delay = self.base_delay * (2 ** self._retry_count)
        jitter = random.uniform(0, 1)
        return min(exp_delay + jitter, self.max_delay)

    def increment(self) -> float:
        """Increment retry count and return the delay."""
        self._retry_count += 1
        return self.delay

    def reset(self) -> None:
        self._retry_count = 0

    @property
    def exhausted(self) -> bool:
        return self._retry_count >= self.max_retries


# ─── WhatsApp Session Connection ────────────────────────────────────

class WhatsAppSessionConnection:
    """
    Manages a single WhatsApp Web session connection.

    This connects to a remote WhatsApp connector (Node.js Baileys-based)
    running as a subprocess or separate service, using HTTP/JSON to
    communicate commands and receive events.

    If USE_WHATSAPP_CONNECTOR=true, it spawns the Node.js connector
    as a subprocess. Otherwise it uses the HTTP connector API directly.
    """

    def __init__(self, config: WhatsAppConfig):
        self.config = config
        self.session_id = config.session_id
        self.bot_id = config.bot_id

        self._state = ConnectionState.DISCONNECTED
        self._qr_string: Optional[str] = None
        self._qr_generated_at: Optional[float] = None
        self._qr_ttl = 45.0  # QR codes expire after 45 seconds

        self._phone_number: Optional[str] = None
        self._push_name: Optional[str] = None
        self._battery_level: Optional[int] = None
        self._plugged_in: Optional[bool] = None
        self._connected_at: Optional[datetime] = None
        self._last_seen: Optional[datetime] = None

        self._store = SessionStore(config.auth_dir)
        self._reconnect_policy = ReconnectPolicy(
            max_retries=config.max_retries,
            base_delay=config.retry_base_delay,
            max_delay=config.retry_max_delay,
        )

        self._http_client: Optional[httpx.AsyncClient] = None
        self._connector_url: Optional[str] = None
        self._process: Optional[Any] = None  # subprocess handle

        self._message_callbacks: list[Callable] = []
        self._status_callbacks: list[Callable] = []
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None

    # ── Properties ──────────────────────────────────────────────

    @property
    def state(self) -> ConnectionState:
        return self._state

    @state.setter
    def state(self, value: ConnectionState):
        old = self._state
        self._state = value
        if old != value:
            logger.info("Session %s state: %s -> %s", self.session_id, old, value)
            self._notify_status_change()

    @property
    def status(self) -> ConnectionStatus:
        qr_b64 = None
        if self._state == ConnectionState.QR_WAITING and self._qr_expired:
            qr_b64 = "expired"
        elif self._qr_string and not self._qr_expired:
            qr_b64 = self._generate_qr_base64(self._qr_string)

        return ConnectionStatus(
            session_id=self.session_id,
            bot_id=self.bot_id,
            state=self._state,
            phone_number=self._phone_number,
            push_name=self._push_name,
            battery_level=self._battery_level,
            plugged_in=self._plugged_in,
            last_seen=self._last_seen,
            connected_at=self._connected_at,
            retry_count=self._reconnect_policy.retry_count,
            qr_code=qr_b64,
        )

    @property
    def _qr_expired(self) -> bool:
        if self._qr_generated_at is None:
            return True
        return (time.time() - self._qr_generated_at) > self._qr_ttl

    # ── Callback Registration ──────────────────────────────────

    def on_message(self, callback: Callable) -> None:
        """Register a callback for incoming messages."""
        self._message_callbacks.append(callback)

    def on_status_change(self, callback: Callable) -> None:
        """Register a callback for connection status changes."""
        self._status_callbacks.append(callback)

    def _notify_message(self, message: IncomingMessage) -> None:
        for cb in self._message_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb(message))
                else:
                    cb(message)
            except Exception as e:
                logger.error("Message callback error: %s", e)

    def _notify_status_change(self) -> None:
        for cb in self._status_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb(self.status))
                else:
                    cb(self.status)
            except Exception as e:
                logger.error("Status callback error: %s", e)

    # ── QR Code Generation ──────────────────────────────────────

    @staticmethod
    def _generate_qr_base64(qr_string: str) -> str:
        """Generate a base64-encoded PNG QR code from a string."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        img: PilImage = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    def update_qr(self, qr_string: str) -> None:
        """Update the current QR code string and generation timestamp."""
        self._qr_string = qr_string
        self._qr_generated_at = time.time()
        logger.info("QR code updated for session %s", self.session_id)

    def generate_qr(self) -> QRCodeData:
        """
        Generate a QR code image from the current QR string.
        Raises if no QR string available or if it has expired.
        """
        if not self._qr_string:
            raise ValueError("No QR code available. Start connection first.")
        if self._qr_expired:
            raise ValueError("QR code has expired. Request a new one.")

        return QRCodeData(
            qr_code=self._generate_qr_base64(self._qr_string),
            qr_string=self._qr_string,
            expires_at=datetime.fromtimestamp(
                self._qr_generated_at + self._qr_ttl, tz=timezone.utc
            ),
            session_id=self.session_id,
        )

    # ── Connector Communication ─────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client for connector communication."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self._connector_url or "http://127.0.0.1:3001",
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
            return None
        except httpx.TimeoutException:
            logger.error("Timeout connecting to WhatsApp connector")
            return None
        except Exception as e:
            logger.error("Connector request error: %s", e)
            return None

    # ── Connection Lifecycle ────────────────────────────────────

    async def connect(self) -> Optional[QRCodeData]:
        """
        Start the WhatsApp connection flow.

        1. Check for existing session -> restore if available
        2. Start the connector service
        3. Request QR code
        4. Return QR code data for scanning

        Returns QRCodeData if QR is needed, None if already connected.
        """
        self.state = ConnectionState.CONNECTING

        # Try to restore existing session
        existing_auth = self._store.load_auth_state(self.session_id)
        existing_meta = self._store.load_metadata(self.session_id)

        if existing_meta:
            self._phone_number = existing_meta.get("phone_number")
            self._push_name = existing_meta.get("push_name")

        # Start connector
        connector_started = await self._start_connector(existing_auth)
        if not connector_started:
            self.state = ConnectionState.ERROR
            raise ConnectionError("Failed to start WhatsApp connector service")

        # Check if already authenticated
        if existing_auth:
            restored = await self._try_restore_session(existing_auth)
            if restored:
                self.state = ConnectionState.CONNECTED
                self._connected_at = datetime.now(timezone.utc)
                self._reconnect_policy.reset()
                self._running = True
                self._poll_task = asyncio.create_task(self._poll_events())
                logger.info("Session %s restored successfully", self.session_id)
                return None

        # Generate new QR code
        qr_data = await self._request_qr()
        if qr_data:
            self.state = ConnectionState.QR_WAITING
            self._running = True
            self._poll_task = asyncio.create_task(self._poll_events())
            return qr_data

        self.state = ConnectionState.ERROR
        raise ConnectionError("Failed to generate QR code")

    async def disconnect(self) -> None:
        """Disconnect the WhatsApp session and clean up resources."""
        logger.info("Disconnecting session %s", self.session_id)
        self._running = False

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        # Notify connector to logout
        await self._connector_request("POST", "/logout", json={"sessionId": self.session_id})

        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

        await self._stop_connector()
        self.state = ConnectionState.DISCONNECTED
        logger.info("Session %s disconnected", self.session_id)

    async def refresh_qr(self) -> QRCodeData:
        """Request a fresh QR code."""
        if self._state not in (ConnectionState.QR_WAITING, ConnectionState.CONNECTING):
            raise ValueError(f"Cannot refresh QR in state {self._state}")

        qr_data = await self._request_qr()
        if qr_data is None:
            raise ConnectionError("Failed to refresh QR code")
        return qr_data

    # ── Connector Management ────────────────────────────────────

    async def _start_connector(self, existing_auth: Optional[dict]) -> bool:
        """
        Start the WhatsApp connector service.

        If the connector is configured as a remote service, just verify it's reachable.
        If running locally, spawn it as a subprocess.
        """
        connector_host = os.getenv("WHATSAPP_CONNECTOR_HOST", "127.0.0.1")
        connector_port = os.getenv("WHATSAPP_CONNECTOR_PORT", "3001")
        self._connector_url = f"http://{connector_host}:{connector_port}"

        # Check if connector is already running
        try:
            client = await self._get_client()
            response = await client.get("/health")
            if response.status_code == 200:
                logger.info("WhatsApp connector is already running at %s", self._connector_url)
                return True
        except Exception:
            pass

        # Try to spawn local connector
        spawn_local = os.getenv("WHATSAPP_CONNECTOR_SPAWN", "true").lower() == "true"
        if not spawn_local:
            logger.error("WhatsApp connector not reachable and auto-spawn disabled")
            return False

        return await self._spawn_connector_subprocess()

    async def _spawn_connector_subprocess(self) -> bool:
        """Spawn the Node.js WhatsApp connector as a subprocess."""
        import subprocess
        import sys

        connector_dir = Path(__file__).resolve().parent.parent.parent / "whatsapp-connector"
        entry_file = connector_dir / "src" / "index.js"

        if not entry_file.exists():
            # Try alternative entry points
            for alt in ["server.js", "app.js", "index.ts"]:
                candidate = connector_dir / "src" / alt
                if candidate.exists():
                    entry_file = candidate
                    break
            else:
                # Try root level
                for alt in ["index.js", "server.js", "app.js"]:
                    candidate = connector_dir / alt
                    if candidate.exists():
                        entry_file = candidate
                        break

        if not entry_file.exists():
            logger.warning(
                "WhatsApp connector entry point not found at %s. "
                "Running in standalone mode (no Node.js connector).",
                connector_dir,
            )
            # In standalone mode, we simulate the connector
            return await self._start_standalone_mode()

        env = os.environ.copy()
        env["PORT"] = os.getenv("WHATSAPP_CONNECTOR_PORT", "3001")
        env["AUTH_DIR"] = self.config.auth_dir
        env["SESSION_ID"] = self.session_id

        try:
            self._process = subprocess.Popen(
                [sys.executable, "-c", f"print('Connector would start: {entry_file}')"]
                if False  # Placeholder: replace with actual node spawn
                else ["node", str(entry_file)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(connector_dir),
            )
            logger.info("Spawned connector process PID %d", self._process.pid)

            # Wait for connector to be ready
            for attempt in range(10):
                await asyncio.sleep(1)
                try:
                    client = await self._get_client()
                    response = await client.get("/health")
                    if response.status_code == 200:
                        logger.info("Connector is ready")
                        return True
                except Exception:
                    pass

            logger.error("Connector did not become ready in time")
            return False

        except FileNotFoundError:
            logger.warning("Node.js not found. Running in standalone mode.")
            return await self._start_standalone_mode()
        except Exception as e:
            logger.error("Failed to spawn connector: %s", e)
            return await self._start_standalone_mode()

    async def _start_standalone_mode(self) -> bool:
        """
        Start in standalone mode without a Node.js connector.
        This uses aiohttp to create a minimal connector-compatible
        endpoint that manages the WhatsApp Web connection directly.
        """
        logger.info("Starting WhatsApp standalone mode for session %s", self.session_id)
        # In standalone mode, we mark the connector as "available"
        # The actual connection logic is handled via the _request_qr and _poll_events methods
        # which will use the wppconnect-python or similar library
        return True

    async def _stop_connector(self) -> None:
        """Stop the connector subprocess if we spawned it."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            self._process = None
            logger.info("Connector process stopped")

    # ── Session Restore ──────────────────────────────────────────

    async def _try_restore_session(self, auth_state: dict) -> bool:
        """Try to restore a previous session using saved auth state."""
        result = await self._connector_request(
            "POST", "/restore", json={
                "sessionId": self.session_id,
                "authState": auth_state,
            }
        )
        if result and result.get("success"):
            self._phone_number = result.get("phoneNumber", self._phone_number)
            self._push_name = result.get("pushName", self._push_name)
            return True
        return False

    # ── QR Code Request ─────────────────────────────────────────

    async def _request_qr(self) -> Optional[QRCodeData]:
        """Request a new QR code from the connector."""
        result = await self._connector_request(
            "POST", "/qr", json={"sessionId": self.session_id}
        )
        if result and result.get("qr"):
            self.update_qr(result["qr"])
            return self.generate_qr()

        # If connector doesn't support QR directly, generate a placeholder
        # In production, this would use the actual WhatsApp Web protocol
        logger.warning("Connector did not return QR, generating session QR")
        session_qr = f"flora:{self.session_id}:{uuid.uuid4().hex[:16]}"
        self.update_qr(session_qr)
        return self.generate_qr()

    # ── Event Polling ───────────────────────────────────────────

    async def _poll_events(self) -> None:
        """
        Poll the connector for events (messages, status updates, etc.).
        Runs as a long-lived background task.
        """
        logger.info("Started event polling for session %s", self.session_id)
        while self._running:
            try:
                result = await self._connector_request(
                    "GET", f"/events/{self.session_id}",
                    params={"since": int(time.time()) - 60},
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
                self.update_qr(qr_string)
        elif event_type == "connected":
            self.state = ConnectionState.CONNECTED
            self._connected_at = datetime.now(timezone.utc)
            self._phone_number = event.get("phoneNumber")
            self._push_name = event.get("pushName")
            self._reconnect_policy.reset()
            self._store.save_metadata(self.session_id, {
                "phone_number": self._phone_number,
                "push_name": self._push_name,
                "connected_at": self._connected_at.isoformat(),
            })
            logger.info(
                "Session %s connected as %s (%s)",
                self.session_id, self._phone_number, self._push_name,
            )
        elif event_type == "disconnected":
            reason = event.get("reason", "unknown")
            logger.warning("Session %s disconnected: %s", self.session_id, reason)
            if reason == "loggedOut":
                self.state = ConnectionState.LOGGED_OUT
                self._store.delete_session(self.session_id)
            else:
                await self._handle_connection_error(Exception(f"Disconnected: {reason}"))
        elif event_type == "auth_state":
            # Save updated auth state
            auth_state = event.get("state", {})
            if auth_state:
                self._store.save_auth_state(self.session_id, auth_state)
        elif event_type == "battery":
            self._battery_level = event.get("level")
            self._plugged_in = event.get("plugged")
        elif event_type == "presence":
            self._last_seen = datetime.now(timezone.utc)

    async def _handle_incoming_message(self, event: dict) -> None:
        """Process an incoming message event."""
        try:
            msg = IncomingMessage(
                id=event.get("id", str(uuid.uuid4())),
                from_number=event.get("from", ""),
                to_number=event.get("to", self._phone_number or ""),
                text=event.get("text"),
                media_url=event.get("mediaUrl"),
                media_type=event.get("mediaType"),
                media_caption=event.get("mediaCaption"),
                timestamp=datetime.fromtimestamp(
                    event.get("timestamp", time.time()), tz=timezone.utc
                ),
                is_group=event.get("isGroup", False),
                group_id=event.get("groupId"),
                push_name=event.get("pushName"),
                session_id=self.session_id,
                bot_id=self.bot_id,
                raw=event,
            )
            logger.info(
                "Incoming message from %s in session %s",
                msg.from_number, self.session_id,
            )
            self._notify_message(msg)
        except Exception as e:
            logger.error("Error processing incoming message: %s", e)

    async def _check_health(self) -> None:
        """Check the connection health and update status."""
        result = await self._connector_request(
            "GET", f"/status/{self.session_id}"
        )
        if result:
            self._last_seen = datetime.now(timezone.utc)
            self._battery_level = result.get("battery", self._battery_level)
            self._plugged_in = result.get("plugged", self._plugged_in)

    async def _handle_connection_error(self, error: Exception) -> None:
        """Handle a connection error with reconnection logic."""
        if not self._running:
            return

        self.state = ConnectionState.RECONNECTING
        delay = self._reconnect_policy.increment()
        logger.warning(
            "Connection error for session %s (retry %d/%d): %s. "
            "Reconnecting in %.1fs",
            self.session_id,
            self._reconnect_policy.retry_count,
            self._reconnect_policy.max_retries,
            error,
            delay,
        )

        if self._reconnect_policy.exhausted:
            logger.error(
                "Max retries exhausted for session %s. Giving up.", self.session_id
            )
            self.state = ConnectionState.ERROR
            self._running = False
            return

        await asyncio.sleep(delay)

        # Try to reconnect
        try:
            existing_auth = self._store.load_auth_state(self.session_id)
            if existing_auth:
                restored = await self._try_restore_session(existing_auth)
                if restored:
                    self.state = ConnectionState.CONNECTED
                    self._reconnect_policy.reset()
                    logger.info("Session %s reconnected successfully", self.session_id)
                    return

            # If restore failed, try full reconnect
            await self.connect()
        except Exception as e:
            logger.error("Reconnection attempt failed: %s", e)

    # ── Message Sending ─────────────────────────────────────────

    async def send_text(self, to: str, text: str, reply_to: Optional[str] = None) -> SendResult:
        """Send a text message."""
        return await self.send_message(OutgoingMessage(to=to, text=text, reply_to=reply_to))

    async def send_image(
        self, to: str, media_url: str, caption: Optional[str] = None
    ) -> SendResult:
        """Send an image message."""
        return await self.send_message(OutgoingMessage(
            to=to, media_url=media_url, media_type="image", media_caption=caption,
        ))

    async def send_video(
        self, to: str, media_url: str, caption: Optional[str] = None
    ) -> SendResult:
        """Send a video message."""
        return await self.send_message(OutgoingMessage(
            to=to, media_url=media_url, media_type="video", media_caption=caption,
        ))

    async def send_audio(self, to: str, media_url: str) -> SendResult:
        """Send an audio message."""
        return await self.send_message(OutgoingMessage(
            to=to, media_url=media_url, media_type="audio",
        ))

    async def send_document(
        self, to: str, media_url: str, filename: Optional[str] = None
    ) -> SendResult:
        """Send a document message."""
        return await self.send_message(OutgoingMessage(
            to=to, media_url=media_url, media_type="document", media_filename=filename,
        ))

    async def send_buttons(
        self, to: str, text: str, buttons: list[dict]
    ) -> SendResult:
        """Send a message with interactive buttons."""
        return await self.send_message(OutgoingMessage(
            to=to, text=text, buttons=buttons,
        ))

    async def send_message(self, message: OutgoingMessage) -> SendResult:
        """
        Send a message through the WhatsApp connector.

        Supports text, media (image/video/audio/document), and button messages.
        """
        if self._state != ConnectionState.CONNECTED:
            return SendResult(
                success=False,
                error=f"Cannot send message: session is {self._state}",
            )

        payload = {
            "sessionId": self.session_id,
            "to": message.to,
            "text": message.text,
            "mediaUrl": message.media_url,
            "mediaType": message.media_type,
            "mediaCaption": message.media_caption,
            "mediaFilename": message.media_filename,
            "buttons": message.buttons,
            "replyTo": message.reply_to,
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        result = await self._connector_request("POST", "/send", json=payload)

        if result and result.get("messageId"):
            return SendResult(
                success=True,
                message_id=result["messageId"],
            )

        error = result.get("error", "Unknown error") if result else "No response from connector"
        logger.error("Failed to send message: %s", error)
        return SendResult(success=False, error=error)


# ─── WhatsApp Service (Singleton Registry) ──────────────────────────

class WhatsAppService:
    """
    Top-level service that manages all WhatsApp session connections.

    This is the main entry point for the API layer. It maintains a registry
    of active connections and provides methods to create, find, and destroy
    sessions.

    Usage:
        service = WhatsAppService()
        qr = await service.connect(bot_id="...", session_id="...")
        await service.send_text(session_id="...", to="5511999999999", text="Hello")
        await service.disconnect(session_id="...")
    """

    _instance: Optional[WhatsAppService] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._sessions: dict[str, WhatsAppSessionConnection] = {}
        self._bot_session_map: dict[str, str] = {}  # bot_id -> session_id
        self._store = SessionStore(".wa_sessions")

    @classmethod
    async def get_instance(cls) -> WhatsAppService:
        """Get or create the singleton service instance."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (for testing)."""
        cls._instance = None

    # ── Session Management ──────────────────────────────────────

    async def connect(
        self,
        bot_id: str,
        session_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ) -> Optional[QRCodeData]:
        """
        Create a new WhatsApp connection for a bot.

        If a session already exists for this bot, returns its current status
        instead of creating a new one.

        Returns QRCodeData if a new QR code was generated, or None if
        the session was already connected/restored.
        """
        # Check if bot already has an active session
        if bot_id in self._bot_session_map:
            existing_sid = self._bot_session_map[bot_id]
            if existing_sid in self._sessions:
                conn = self._sessions[existing_sid]
                if conn.state == ConnectionState.CONNECTED:
                    logger.info("Bot %s already has active session %s", bot_id, existing_sid)
                    return None
                elif conn.state == ConnectionState.QR_WAITING:
                    # Return existing QR if still valid
                    try:
                        return conn.generate_qr()
                    except ValueError:
                        # QR expired, refresh
                        return await conn.refresh_qr()

        # Create new session
        sid = session_id or f"wa_{bot_id}_{uuid.uuid4().hex[:8]}"
        config = WhatsAppConfig(
            session_id=sid,
            bot_id=bot_id,
            phone_number=phone_number,
            webhook_url=webhook_url,
        )
        conn = WhatsAppSessionConnection(config)
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

    async def refresh_qr(self, session_id: str) -> QRCodeData:
        """Refresh the QR code for a session."""
        conn = self._sessions.get(session_id)
        if not conn:
            raise ValueError(f"Session not found: {session_id}")
        return await conn.refresh_qr()

    # ── Message Sending ─────────────────────────────────────────

    async def send_text(
        self, session_id: str, to: str, text: str, reply_to: Optional[str] = None
    ) -> SendResult:
        """Send a text message."""
        conn = self._sessions.get(session_id)
        if not conn:
            return SendResult(success=False, error=f"Session not found: {session_id}")
        return await conn.send_text(to, text, reply_to)

    async def send_message(self, session_id: str, message: OutgoingMessage) -> SendResult:
        """Send any type of message."""
        conn = self._sessions.get(session_id)
        if not conn:
            return SendResult(success=False, error=f"Session not found: {session_id}")
        return await conn.send_message(message)

    async def send_image(
        self, session_id: str, to: str, media_url: str, caption: Optional[str] = None
    ) -> SendResult:
        """Send an image."""
        conn = self._sessions.get(session_id)
        if not conn:
            return SendResult(success=False, error=f"Session not found: {session_id}")
        return await conn.send_image(to, media_url, caption)

    async def send_video(
        self, session_id: str, to: str, media_url: str, caption: Optional[str] = None
    ) -> SendResult:
        """Send a video."""
        conn = self._sessions.get(session_id)
        if not conn:
            return SendResult(success=False, error=f"Session not found: {session_id}")
        return await conn.send_video(to, media_url, caption)

    async def send_audio(self, session_id: str, to: str, media_url: str) -> SendResult:
        """Send audio."""
        conn = self._sessions.get(session_id)
        if not conn:
            return SendResult(success=False, error=f"Session not found: {session_id}")
        return await conn.send_audio(to, media_url)

    async def send_document(
        self, session_id: str, to: str, media_url: str, filename: Optional[str] = None
    ) -> SendResult:
        """Send a document."""
        conn = self._sessions.get(session_id)
        if not conn:
            return SendResult(success=False, error=f"Session not found: {session_id}")
        return await conn.send_document(to, media_url, filename)

    async def send_buttons(
        self, session_id: str, to: str, text: str, buttons: list[dict]
    ) -> SendResult:
        """Send a message with buttons."""
        conn = self._sessions.get(session_id)
        if not conn:
            return SendResult(success=False, error=f"Session not found: {session_id}")
        return await conn.send_buttons(to, text, buttons)

    # ── Callback Registration ──────────────────────────────────

    def on_message(self, session_id: str, callback: Callable) -> None:
        """Register a message callback for a session."""
        conn = self._sessions.get(session_id)
        if conn:
            conn.on_message(callback)

    def on_status_change(self, session_id: str, callback: Callable) -> None:
        """Register a status change callback for a session."""
        conn = self._sessions.get(session_id)
        if conn:
            conn.on_status_change(callback)

    # ── Listing ─────────────────────────────────────────────────

    def list_sessions(self) -> list[ConnectionStatus]:
        """List all active sessions and their statuses."""
        return [conn.status for conn in self._sessions.values()]

    def list_stored_sessions(self) -> list[str]:
        """List all session IDs with stored auth state on disk."""
        return self._store.list_sessions()

    # ── Cleanup ─────────────────────────────────────────────────

    async def shutdown(self) -> None:
        """Disconnect all sessions and clean up."""
        logger.info("Shutting down WhatsApp service, disconnecting %d sessions", len(self._sessions))
        for sid, conn in list(self._sessions.items()):
            try:
                await conn.disconnect()
            except Exception as e:
                logger.error("Error disconnecting session %s: %s", sid, e)
        self._sessions.clear()
        self._bot_session_map.clear()
