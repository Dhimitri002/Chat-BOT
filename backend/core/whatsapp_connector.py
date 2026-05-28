"""
Flora Platform — WhatsApp Connector Interface
==============================================
Abstract base class for WhatsApp connection backends,
plus concrete implementations for different providers.

Supported backends:
  - BaileysConnector: Connects to a Baileys/WhatsApp-Web bridge service
  - WhatsAppBusinessAPIConnector: Meta Cloud API connector
  - ConnectorFactory: Creates the right connector based on config

Usage:
    connector = ConnectorFactory.create("baileys", config)
    await connector.connect()
    qr = await connector.get_qr()
    await connector.send_text(to="+1234567890", text="Hello")
    await connector.disconnect()
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Optional

import httpx
import qrcode
from pydantic import BaseModel, Field

from backend.config import settings

logger = logging.getLogger(__name__)


# ─── Connector State ────────────────────────────────────────────────

class ConnectorState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    QR_WAITING = "qr_waiting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    LOGGED_OUT = "logged_out"
    ERROR = "error"


# ─── Data Models ────────────────────────────────────────────────────

class ConnectorMessage(BaseModel):
    """Normalized message from any connector backend."""
    id: str
    from_number: str
    to_number: str
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_group: bool = False
    push_name: Optional[str] = None
    raw: dict = Field(default_factory=dict)


class ConnectorEvent(BaseModel):
    """A connector event (state change, message, QR, etc.)."""
    type: str
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict = Field(default_factory=dict)



# ─── Abstract Connector ─────────────────────────────────────────────

class BaseWhatsAppConnector(ABC):
    """
    Abstract base class for WhatsApp connection backends.

    All connectors must implement these methods to provide a unified
    interface for the WhatsAppService to work with.
    """

    def __init__(self, session_id: str, bot_id: str, config: dict | None = None):
        self.session_id = session_id
        self.bot_id = bot_id
        self.config = config or {}
        self.state = ConnectorState.DISCONNECTED
        self._phone_number: Optional[str] = None
        self._push_name: Optional[str] = None
        self._event_handlers: list[Callable] = []
        self._connected_at: Optional[datetime] = None
        self._last_seen: Optional[datetime] = None
        self._qr_string: Optional[str] = None
        self._qr_expires: Optional[datetime] = None

    # ── Event Handling ──────────────────────────────────────────

    def on_event(self, handler: Callable):
        """Register an event handler."""
        self._event_handlers.append(handler)

    def off_event(self, handler: Callable):
        """Unregister an event handler."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    async def _emit_event(self, event_type: str, data: dict | None = None):
        """Emit an event to all registered handlers."""
        event_data = {
            "type": event_type,
            "session_id": self.session_id,
            "bot_id": self.bot_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        }
        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.error("Event handler error: %s", e)

    # ── Abstract Methods ────────────────────────────────────────

    @abstractmethod
    async def connect(self) -> Optional[str]:
        """
        Start the connection process.
        Returns a QR code string if authentication is needed, None otherwise.
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect and clean up resources."""
        ...

    @abstractmethod
    async def send_text(self, to: str, text: str, reply_to: Optional[str] = None) -> dict:
        """Send a text message. Returns dict with messageId or error."""
        ...

    @abstractmethod
    async def send_media(
        self,
        to: str,
        media_url: str,
        media_type: str = "image",
        caption: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> dict:
        """Send a media message."""
        ...

    @abstractmethod
    async def get_qr(self) -> Optional[str]:
        """Get the current QR code string."""
        ...

    @abstractmethod
    async def get_state(self) -> ConnectorState:
        """Get the current connection state."""
        ...

    @abstractmethod
    async def restore_session(self, auth_state: dict) -> bool:
        """Restore a session from saved auth state. Returns True on success."""
        ...

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if the session is currently connected."""
        ...

    async def get_qr_image(self) -> Optional[str]:
        """Generate a base64-encoded PNG QR code image from the current QR string."""
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

    @property
    def phone_number(self) -> Optional[str]:
        return self._phone_number

    @property
    def push_name(self) -> Optional[str]:
        return self._push_name

    @property
    def connected_at(self) -> Optional[datetime]:
        return self._connected_at

    @property
    def last_seen(self) -> Optional[datetime]:
        return self._last_seen


# ─── Baileys/Bridge Connector ──────────────────────────────────────

class BaileysConnector(BaseWhatsAppConnector):
    """
    Connector that communicates with a Baileys/WhatsApp-Web bridge service
    over HTTP. This is the default connector for Flora Platform.

    The bridge service runs separately and provides a REST API for WhatsApp
    Web operations (similar to what wppconnect-server provides).
    """

    def __init__(self, session_id: str, bot_id: str, config: dict | None = None):
        super().__init__(session_id, bot_id, config)
        self._connector_url = (
            config.get("connector_url")
            or getattr(settings, "WHATSAPP_CONNECTOR_URL", None)
            or "http://127.0.0.1:3333"
        )
        self._connector_token = config.get("connector_token") or getattr(
            settings, "WHATSAPP_CONNECTOR_TOKEN", ""
        )
        self._timeout = config.get("timeout", 15)
        self._http_client: Optional[httpx.AsyncClient] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._disconnect_event = asyncio.Event()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self._connector_token:
                headers["Authorization"] = f"Bearer {self._connector_token}"
            self._http_client = httpx.AsyncClient(
                base_url=self._connector_url,
                timeout=httpx.Timeout(self._timeout),
                headers=headers,
            )
        return self._http_client

    async def _request(self, method: str, path: str, **kwargs) -> Optional[dict]:
        """Make an HTTP request to the bridge service."""
        client = await self._get_client()
        try:
            response = await client.request(method, path, **kwargs)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning("Session not found on bridge: %s", self.session_id)
                return None
            elif response.status_code == 429:
                logger.warning("Rate limited by bridge service")
                await asyncio.sleep(2)
                return None
            else:
                logger.warning(
                    "Bridge returned %d for %s %s: %s",
                    response.status_code, method, path, response.text[:200],
                )
                return None
        except httpx.ConnectError:
            logger.error("Cannot connect to WhatsApp bridge at %s", self._connector_url)
            await self._emit_event("error", {"message": f"Cannot reach bridge at {self._connector_url}"})
            return None
        except httpx.TimeoutException:
            logger.error("Timeout connecting to WhatsApp bridge")
            await self._emit_event("error", {"message": "Bridge timeout"})
            return None
        except Exception as e:
            logger.error("Bridge request error: %s", e)
            return None

    async def connect(self) -> Optional[str]:
        """
        Start a new session on the bridge.
        Returns QR string if needed, None if connected immediately.
        """
        self.state = ConnectorState.CONNECTING
        await self._emit_event("state_change", {"state": "connecting"})

        result = await self._request(
            "POST",
            "/session/start",
            json={"sessionId": self.session_id, "botId": self.bot_id},
        )

        if not result:
            self.state = ConnectorState.ERROR
            await self._emit_event("error", {"message": "Failed to start session on bridge"})
            raise ConnectionError(
                "Could not start WhatsApp session on bridge. Is the bridge service running?"
            )

        if result.get("qr"):
            self._qr_string = result["qr"]
            self._qr_expires = datetime.now(timezone.utc) + timedelta(
                seconds=result.get("expiresIn", 60)
            )
            self.state = ConnectorState.QR_WAITING
            await self._emit_event("qr", {"qr": result["qr"], "expiresIn": result.get("expiresIn", 60)})
            # Start polling for events
            self._start_polling()
            return result["qr"]

        if result.get("connected"):
            self._phone_number = result.get("phoneNumber", "")
            self._push_name = result.get("pushName", "")
            self._connected_at = datetime.now(timezone.utc)
            self.state = ConnectorState.CONNECTED
            self._start_polling()
            await self._emit_event("connected", {"phone": self._phone_number, "name": self._push_name})
            return None

        self.state = ConnectorState.ERROR
        await self._emit_event("error", {"message": "Unexpected bridge response"})
        raise ConnectionError("Unexpected response from WhatsApp bridge")

    async def disconnect(self) -> None:
        """Disconnect the session."""
        self._disconnect_event.set()
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        await self._request(
            "POST", "/session/disconnect", json={"sessionId": self.session_id}
        )

        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

        self.state = ConnectorState.DISCONNECTED
        await self._emit_event("state_change", {"state": "disconnected"})

    async def send_text(self, to: str, text: str, reply_to: Optional[str] = None) -> dict:
        """Send a text message through the bridge."""
        payload = {
            "sessionId": self.session_id,
            "to": self._format_phone(to),
            "text": text,
        }
        if reply_to:
            payload["replyTo"] = reply_to

        result = await self._request("POST", "/message/send", json=payload)
        if result and result.get("messageId"):
            return {"success": True, "messageId": result["messageId"]}
        return {"success": False, "error": result.get("error", "Unknown error") if result else "No response"}

    async def send_media(
        self,
        to: str,
        media_url: str,
        media_type: str = "image",
        caption: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> dict:
        """Send a media message through the bridge."""
        payload = {
            "sessionId": self.session_id,
            "to": self._format_phone(to),
            "mediaUrl": media_url,
            "mediaType": media_type,
        }
        if caption:
            payload["caption"] = caption
        if filename:
            payload["filename"] = filename

        result = await self._request("POST", "/message/send", json=payload)
        if result and result.get("messageId"):
            return {"success": True, "messageId": result["messageId"]}
        return {"success": False, "error": result.get("error", "Unknown error") if result else "No response"}

    async def get_qr(self) -> Optional[str]:
        """Get the current QR code string, refreshing if needed."""
        if self._qr_string and self._qr_expires and datetime.now(timezone.utc) < self._qr_expires:
            return self._qr_string

        # Request a fresh QR from the bridge
        result = await self._request(
            "POST", "/session/qr", json={"sessionId": self.session_id}
        )
        if result and result.get("qr"):
            self._qr_string = result["qr"]
            self._qr_expires = datetime.now(timezone.utc) + timedelta(
                seconds=result.get("expiresIn", 60)
            )
            return self._qr_string
        return None

    async def get_state(self) -> ConnectorState:
        """Get the current connection state from the bridge."""
        result = await self._request("GET", f"/session/{self.session_id}/status")
        if result:
            state_map = {
                "disconnected": ConnectorState.DISCONNECTED,
                "connecting": ConnectorState.CONNECTING,
                "qr_waiting": ConnectorState.QR_WAITING,
                "connected": ConnectorState.CONNECTED,
                "reconnecting": ConnectorState.RECONNECTING,
                "logged_out": ConnectorState.LOGGED_OUT,
                "error": ConnectorState.ERROR,
            }
            new_state = state_map.get(result.get("status", ""), self.state)
            if new_state != self.state:
                self.state = new_state
            if result.get("phoneNumber"):
                self._phone_number = result["phoneNumber"]
            if result.get("pushName"):
                self._push_name = result["pushName"]
        return self.state

    async def restore_session(self, auth_state: dict) -> bool:
        """Try to restore a session using saved auth state."""
        result = await self._request(
            "POST",
            "/session/restore",
            json={
                "sessionId": self.session_id,
                "botId": self.bot_id,
                "state": auth_state,
            },
        )

        if result and result.get("connected"):
            self._phone_number = result.get("phoneNumber", "")
            self._push_name = result.get("pushName", "")
            self._connected_at = datetime.now(timezone.utc)
            self.state = ConnectorState.CONNECTED
            self._start_polling()
            await self._emit_event("connected", {"phone": self._phone_number, "name": self._push_name})
            return True

        if result and result.get("qr"):
            # Bridge needs a new QR - restore failed
            self._qr_string = result["qr"]
            self._qr_expires = datetime.now(timezone.utc) + timedelta(
                seconds=result.get("expiresIn", 60)
            )
            self.state = ConnectorState.QR_WAITING
            await self._emit_event("qr", {"qr": result["qr"], "expiresIn": result.get("expiresIn", 60)})
            self._start_polling()
            return False

        return False

    async def is_connected(self) -> bool:
        """Check if the session is connected."""
        state = await self.get_state()
        return state == ConnectorState.CONNECTED

    def _start_polling(self):
        """Start polling the bridge for events."""
        if self._poll_task and not self._poll_task.done():
            return
        self._poll_task = asyncio.create_task(self._poll_events())

    async def _poll_events(self):
        """Poll the bridge for events (QR scan, incoming messages, disconnections)."""
        while not self._disconnect_event.is_set():
            try:
                result = await self._request(
                    "GET",
                    f"/session/{self.session_id}/events",
                )

                if result:
                    events = result.get("events", [])
                    for event in events:
                        await self._handle_bridge_event(event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Event polling error: %s", e)

            # Also check health
            try:
                health = await self._request("GET", f"/session/{self.session_id}/health")
                if health and health.get("status") == "healthy":
                    self._last_seen = datetime.now(timezone.utc)
            except Exception:
                pass

            await asyncio.sleep(2)

    async def _handle_bridge_event(self, event: dict):
        """Process an event from the bridge."""
        event_type = event.get("type", "")

        if event_type == "message":
            msg_data = event.get("data", {})
            await self._emit_event("message", msg_data)
        elif event_type == "qr":
            self._qr_string = event.get("qr", "")
            self._qr_expires = datetime.now(timezone.utc) + timedelta(
                seconds=event.get("expiresIn", 60)
            )
            self.state = ConnectorState.QR_WAITING
            await self._emit_event("qr", {"qr": self._qr_string})
        elif event_type == "connected":
            self._phone_number = event.get("phoneNumber", "")
            self._push_name = event.get("pushName", "")
            self._connected_at = datetime.now(timezone.utc)
            self._last_seen = datetime.now(timezone.utc)
            self.state = ConnectorState.CONNECTED
            self._qr_string = None
            self._qr_expires = None
            await self._emit_event("connected", {"phone": self._phone_number, "name": self._push_name})
        elif event_type == "disconnected":
            reason = event.get("reason", "unknown")
            if reason == "loggedOut":
                self.state = ConnectorState.LOGGED_OUT
            else:
                self.state = ConnectorState.DISCONNECTED
            await self._emit_event("disconnected", {"reason": reason})
        elif event_type == "connection.update":
            status = event.get("status", "")
            if status == "open":
                self.state = ConnectorState.CONNECTED
            elif status == "close":
                reason = event.get("reason", "")
                self.state = ConnectorState.LOGGED_OUT if reason == "loggedOut" else ConnectorState.DISCONNECTED
            await self._emit_event("state_change", {"state": self.state.value})
        elif event_type == "creds.update":
            # Auth state was updated
            creds = event.get("state")
            if creds:
                await self._emit_event("creds_update", creds)

        self._last_seen = datetime.now(timezone.utc)

    @staticmethod
    def _format_phone(phone: str) -> str:
        return phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")


# ─── Meta Cloud API Connector (Business API) ──────────────────────

class WhatsAppBusinessAPIConnector(BaseWhatsAppConnector):
    """
    Connector for the Meta WhatsApp Business Cloud API.
    This connector uses the official HTTP API from Meta.

    Configuration needs:
        - access_token: Permanent access token from Meta
        - phone_number_id: The phone number ID from the API setup
        - business_account_id: The WABA ID
    """

    CLOUD_API_BASE = "https://graph.facebook.com/v18.0"

    def __init__(self, session_id: str, bot_id: str, config: dict | None = None):
        super().__init__(session_id, bot_id, config)
        self._access_token = config.get("access_token", "")
        self._phone_number_id = config.get("phone_number_id", "")
        self._business_account_id = config.get("business_account_id", "")
        self._http_client: Optional[httpx.AsyncClient] = None
        if not self._access_token or not self._phone_number_id:
            raise ValueError(
                "WhatsAppBusinessAPIConnector requires 'access_token' and 'phone_number_id' in config"
            )

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.CLOUD_API_BASE,
                timeout=httpx.Timeout(30),
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                },
            )
        return self._http_client

    async def _request(self, method: str, path: str, **kwargs) -> Optional[dict]:
        client = await self._get_client()
        try:
            response = await client.request(method, path, **kwargs)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Meta API rate limit hit")
                await asyncio.sleep(5)
                return None
            else:
                logger.warning("Meta API returned %d: %s", response.status_code, response.text[:200])
                return None
        except Exception as e:
            logger.error("Meta API error: %s", e)
            return None

    async def connect(self) -> Optional[str]:
        """
        Verify the connection is valid.
        Cloud API doesn't use QR codes - it's token-based.
        """
        self.state = ConnectorState.CONNECTING
        # Verify the phone number configuration
        result = await self._request("GET", f"/{self._phone_number_id}")
        if result and result.get("verified_name"):
            self._phone_number = result.get("display_phone_number", self._phone_number_id)
            self._push_name = result.get("verified_name", "")
            self._connected_at = datetime.now(timezone.utc)
            self.state = ConnectorState.CONNECTED
            await self._emit_event("connected", {"phone": self._phone_number, "name": self._push_name})
            return None
        self.state = ConnectorState.ERROR
        await self._emit_event("error", {"message": "Could not verify WhatsApp Business API connection"})
        raise ConnectionError("Could not verify WhatsApp Business API connection")

    async def disconnect(self) -> None:
        """Mark as disconnected for Cloud API (no persistent connection)."""
        self.state = ConnectorState.DISCONNECTED
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        await self._emit_event("state_change", {"state": "disconnected"})

    async def send_text(self, to: str, text: str, reply_to: Optional[str] = None) -> dict:
        """
        Send a text message via the Cloud API.
        Note: Can only send template messages to users who haven't messaged
        you in the last 24 hours (WhatsApp policy).
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": self._format_phone(to),
            "type": "text",
            "text": {"body": text},
        }
        if reply_to:
            payload["context"] = {"message_id": reply_to}

        result = await self._request(
            "POST",
            f"/{self._phone_number_id}/messages",
            json=payload,
        )
        if result and result.get("messages"):
            return {"success": True, "messageId": result["messages"][0]["id"]}
        return {"success": False, "error": result.get("error", {}).get("message", "Unknown error") if result else "No response"}

    async def send_media(
        self,
        to: str,
        media_url: str,
        media_type: str = "image",
        caption: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> dict:
        """Send a media message via the Cloud API."""
        type_map = {
            "image": "image",
            "video": "video",
            "audio": "audio",
            "document": "document",
        }
        api_type = type_map.get(media_type, "document")

        media_payload = {"link": media_url}
        if caption and api_type in ("image", "video", "document"):
            media_payload["caption"] = caption
        if filename and api_type == "document":
            media_payload["filename"] = filename

        payload = {
            "messaging_product": "whatsapp",
            "to": self._format_phone(to),
            "type": api_type,
            api_type: media_payload,
        }

        result = await self._request(
            "POST",
            f"/{self._phone_number_id}/messages",
            json=payload,
        )
        if result and result.get("messages"):
            return {"success": True, "messageId": result["messages"][0]["id"]}
        return {"success": False, "error": result.get("error", {}).get("message", "Unknown error") if result else "No response"}

    async def get_qr(self) -> Optional[str]:
        """Cloud API doesn't use QR codes."""
        return None

    async def get_state(self) -> ConnectorState:
        """Check if the Cloud API is reachable."""
        result = await self._request("GET", f"/{self._phone_number_id}")
        if result:
            self.state = ConnectorState.CONNECTED
        else:
            self.state = ConnectorState.ERROR
        return self.state

    async def restore_session(self, auth_state: dict) -> bool:
        """For Cloud API, just verify the token is still valid."""
        return await self.is_connected()

    async def is_connected(self) -> bool:
        """Check if the Cloud API token is valid."""
        result = await self._request("GET", f"/{self._phone_number_id}")
        return result is not None

    @staticmethod
    def _format_phone(phone: str) -> str:
        return phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")


# ─── Connector Factory ──────────────────────────────────────────────

class ConnectorFactory:
    """Factory to create the appropriate WhatsApp connector."""

    _registry: dict[str, type[BaseWhatsAppConnector]] = {
        "baileys": BaileysConnector,
        "whatsapp_business_api": WhatsAppBusinessAPIConnector,
        "cloud_api": WhatsAppBusinessAPIConnector,
    }

    @classmethod
    def register(cls, name: str, connector_class: type[BaseWhatsAppConnector]):
        """Register a new connector type."""
        cls._registry[name] = connector_class

    @classmethod
    def create(
        cls,
        backend: str,
        session_id: str,
        bot_id: str,
        config: dict | None = None,
    ) -> BaseWhatsAppConnector:
        """
        Create a connector instance.

        Args:
            backend: Connector type name ("baileys", "whatsapp_business_api", etc.)
            session_id: Unique session identifier
            bot_id: Bot ID this session belongs to
            config: Additional configuration dict

        Returns:
            A connector instance

        Raises:
            ValueError: If the backend type is not registered
        """
        connector_class = cls._registry.get(backend)
        if not connector_class:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Unknown WhatsApp connector backend: '{backend}'. Available: {available}"
            )
        return connector_class(session_id, bot_id, config)

    @classmethod
    def available_backends(cls) -> list[str]:
        """List all registered connector backend names."""
        return list(cls._registry.keys())
