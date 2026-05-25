"""
WhatsApp Python Bridge — Flora Platform
========================================
Manages the lifecycle of the Node.js WhatsApp connector subprocess.
Communicates via stdin/stdout JSON protocol.

Communication Protocol:
    Python → Node.js (stdin):
        {"type": "send_message", "to": "5511999999999", "message": "Hello", "message_id": "uuid"}
        {"type": "send_media", "to": "...", "media_data": "base64...", "media_type": "image", ...}
        {"type": "disconnect"}
        {"type": "check_status"}

    Node.js → Python (stdout):
        {"type": "qr", "qr": "..."}
        {"type": "connected", "phone_number": "...", "phone_name": "..."}
        {"type": "disconnected", "reason": "...", "statusCode": 401}
        {"type": "message", "data": {...}}
        {"type": "message_sent", "message_id": "...", "wa_message_id": "..."}
        {"type": "send_error", "message_id": "...", "error": "..."}
        {"type": "error", "message": "...", "fatal": false}
        {"type": "status", "connected": true, "phone_number": "..."}
        {"type": "reconnecting", "attempt": 1, "delay": 2000}

Usage:
    bridge = Bridge()
    await bridge.start()

    # Send a message
    await bridge.send_message("5511999999999", "Hello!", message_id="msg-001")

    # Set callbacks
    bridge.on_qr = lambda qr: print(f"QR: {qr}")
    bridge.on_connected = lambda data: print(f"Connected: {data}")
    bridge.on_message = lambda msg: print(f"Message: {msg}")
    bridge.on_disconnected = lambda data: print(f"Disconnected: {data}")

    # Stop
    await bridge.stop()
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

from .config import (
    NODE_SCRIPT,
    BOT_ID,
    SESSION_ID,
    AUTH_DIR,
    LOG_LEVEL,
    CALLBACK_TIMEOUT,
    MAX_RECONNECT_TRIES,
    INITIAL_RETRY_DELAY,
    MAX_RETRY_DELAY,
    BACKOFF_MULTIPLIER,
)

logger = logging.getLogger(__name__)


class BridgeState(str, Enum):
    """Connection states for the Python bridge."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    WAITING_QR = "waiting_qr"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    STOPPED = "stopped"
    ERROR = "error"


_JSONPacket = dict[str, Any]
_JsonCallback = Callable[[_JSONPacket], Awaitable[None]]


class Bridge:
    """
    Manages the WhatsApp connector subprocess lifecycle.

    Usage:
        bridge = Bridge()
        bridge.on_qr = handle_qr
        bridge.on_connected = handle_connected
        bridge.on_message = handle_message
        await bridge.start()
        # ... use bridge ...
        await bridge.stop()
    """

    def __init__(
        self,
        node_script: Optional[str] = None,
        bot_id: Optional[str] = None,
        session_id: Optional[str] = None,
        auth_dir: Optional[str] = None,
    ):
        # Configuration
        self._node_script = node_script or NODE_SCRIPT
        self._bot_id = bot_id or BOT_ID
        self._session_id = session_id or SESSION_ID
        self._auth_dir = auth_dir or AUTH_DIR

        # State
        self._state = BridgeState.DISCONNECTED
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._reconnect_count = 0
        self._closed = False
        self._phone_number: Optional[str] = None
        self._phone_name: Optional[str] = None

        # Callbacks
        self.on_qr: Optional[Callable[[str], Any]] = None
        self.on_qr_expired: Optional[Callable[[], Any]] = None
        self.on_connected: Optional[Callable[[dict], Any]] = None
        self.on_message: Optional[Callable[[dict], Any]] = None
        self.on_disconnected: Optional[Callable[[dict], Any]] = None
        self.on_reconnecting: Optional[Callable[[dict], Any]] = None
        self.on_error: Optional[Callable[[dict], Any]] = None
        self.on_send_error: Optional[Callable[[dict], Any]] = None
        self.on_message_sent: Optional[Callable[[dict], Any]] = None
        self.on_group_participants: Optional[Callable[[dict], Any]] = None
        self.on_presence: Optional[Callable[[dict], Any]] = None
        self.on_creds_update: Optional[Callable[[], Any]] = None

        # Pending send callbacks (message_id -> asyncio.Future)
        self._pending_sends: dict[str, asyncio.Future] = {}

    @property
    def state(self) -> BridgeState:
        """Current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Whether the bridge is connected to WhatsApp."""
        return self._state == BridgeState.CONNECTED

    @property
    def phone_number(self) -> Optional[str]:
        """Connected phone number (when connected)."""
        return self._phone_number

    @property
    def phone_name(self) -> Optional[str]:
        """Connected profile name (when connected)."""
        return self._phone_name

    async def start(self) -> None:
        """Start the Node.js connector subprocess and begin reading stdout."""
        if self._closed:
            raise RuntimeError("Bridge has been closed. Create a new instance.")
        if self._state not in (BridgeState.DISCONNECTED, BridgeState.ERROR, BridgeState.STOPPED):
            logger.warning(f"Bridge already running (state={self._state})")
            return

        self._state = BridgeState.CONNECTING
        logger.info("Starting WhatsApp connector subprocess...", extra={
            "node_script": self._node_script,
            "bot_id": self._bot_id,
            "session_id": self._session_id,
        })

        try:
            self._process = await asyncio.create_subprocess_exec(
                "node",
                self._node_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                env={
                    "NODE_ENV": "production",
                    "SESSION_ID": self._session_id,
                    "BOT_ID": self._bot_id,
                    "AUTH_DIR": self._auth_dir,
                    "LOG_LEVEL": LOG_LEVEL,
                    "PATH": "",  # Clear PATH for security
                },
            )

            # Monitor stderr for debugging
            asyncio.create_task(self._read_stderr())

            # Start reading stdout
            self._reader_task = asyncio.create_task(self._read_stdout())
            logger.info(f"Connector subprocess started (PID: {self._process.pid})")

        except FileNotFoundError:
            self._state = BridgeState.ERROR
            logger.error("Node.js not found. Is Node.js installed? (node --version)")
            raise RuntimeError("Node.js not found. Please install Node.js.")
        except Exception as e:
            self._state = BridgeState.ERROR
            logger.error(f"Failed to start connector: {e}")
            raise

    async def stop(self) -> None:
        """Gracefully stop the connector subprocess."""
        logger.info("Stopping bridge...")
        self._closed = True
        self._state = BridgeState.STOPPED

        # Cancel reader task
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        # Send disconnect command to Node.js
        if self._process and self._process.returncode is None:
            try:
                await self._send_command({"type": "disconnect"})
            except Exception:
                pass

            # Give graceful shutdown a moment
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                logger.warning("Graceful shutdown timed out, killing process")
                self._process.kill()
                await self._process.wait()

        # Resolve any pending sends with error
        for msg_id, fut in list(self._pending_sends.items()):
            if not fut.done():
                fut.set_exception(RuntimeError("Bridge stopped"))

        self._process = None
        self._reconnect_count = 0
        logger.info("Bridge stopped")

    async def send_message(self, to: str, message: str, message_id: Optional[str] = None) -> dict:
        """
        Send a text message.

        Args:
            to: Phone number (with country code, e.g. "5511999999999")
            message: Text message to send
            message_id: Optional ID for tracking

        Returns:
            dict with send confirmation data

        Raises:
            RuntimeError: If not connected or bridge is stopped
        """
        if self._state == BridgeState.STOPPED:
            raise RuntimeError("Bridge is stopped")

        mid = message_id or str(uuid.uuid4())
        cmd = {
            "type": "send_message",
            "to": to,
            "message": message,
            "message_id": mid,
        }

        logger.debug(f"Sending message {mid} to {to}")

        # Create a future that resolves when Node.js confirms send
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self._pending_sends[mid] = fut

        try:
            await self._send_command(cmd)
            result = await asyncio.wait_for(fut, timeout=CALLBACK_TIMEOUT)
            return result
        except asyncio.TimeoutError:
            self._pending_sends.pop(mid, None)
            raise RuntimeError(f"Send confirmation timeout for message {mid}")
        except Exception as e:
            self._pending_sends.pop(mid, None)
            raise

    async def send_media(
        self,
        to: str,
        media_data_b64: str,
        media_type: str = "image",
        caption: str = "",
        mimetype: str = "application/octet-stream",
        file_name: str = "document",
        message_id: Optional[str] = None,
    ) -> dict:
        """
        Send a media message.

        Args:
            to: Phone number
            media_data_b64: Base64-encoded media file data
            media_type: One of "image", "video", "audio", "document"
            caption: Optional caption (used for image/video)
            mimetype: MIME type for documents
            file_name: File name for documents
            message_id: Optional tracking ID

        Returns:
            dict with send confirmation data
        """
        if self._state == BridgeState.STOPPED:
            raise RuntimeError("Bridge is stopped")

        mid = message_id or str(uuid.uuid4())
        cmd = {
            "type": "send_media",
            "to": to,
            "media_data": media_data_b64,
            "media_type": media_type,
            "caption": caption,
            "mimetype": mimetype,
            "file_name": file_name,
            "message_id": mid,
        }

        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self._pending_sends[mid] = fut

        try:
            await self._send_command(cmd)
            result = await asyncio.wait_for(fut, timeout=CALLBACK_TIMEOUT)
            return result
        except asyncio.TimeoutError:
            self._pending_sends.pop(mid, None)
            raise RuntimeError(f"Send confirmation timeout for media {mid}")
        except Exception as e:
            self._pending_sends.pop(mid, None)
            raise

    async def check_status(self) -> dict:
        """Request current connection status from Node.js."""
        return await self._send_command_with_response({"type": "check_status"})

    # ── Internal Methods ────────────────────────────────────────────

    async def _send_command(self, cmd: dict) -> None:
        """Send a JSON command to Node.js via stdin."""
        if not self._process or self._process.stdin.is_closing():
            raise RuntimeError("Node.js process not available")

        line = json.dumps(cmd, ensure_ascii=False) + "\n"
        self._process.stdin.write(line.encode("utf-8"))
        await self._process.stdin.drain()

    async def _send_command_with_response(self, cmd: dict, timeout: float = 10.0) -> dict:
        """Send a command and wait for a matching response."""
        if not self._process or self._process.stdin.is_closing():
            raise RuntimeError("Node.js process not available")

        cmd_id = str(uuid.uuid4())
        cmd["_cmd_id"] = cmd_id

        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self._pending_sends[cmd_id] = fut

        try:
            await self._send_command(cmd)
            result = await asyncio.wait_for(fut, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            self._pending_sends.pop(cmd_id, None)
            raise RuntimeError(f"Command response timeout: {cmd['type']}")
        except Exception as e:
            self._pending_sends.pop(cmd_id, None)
            raise

    async def _read_stdout(self) -> None:
        """Read and process JSON lines from Node.js stdout."""
        logger.debug("Stdout reader started")
        try:
            while not self._closed:
                if not self._process or not self._process.stdout:
                    break

                try:
                    line_bytes = await self._process.stdout.readline()
                except (asyncio.CancelledError, Exception):
                    break

                if not line_bytes:
                    # EOF — process exited
                    logger.warning("Node.js process stdout closed (EOF)")
                    break

                line = line_bytes.decode("utf-8").strip()
                if not line:
                    continue

                try:
                    packet = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from Node.js: {line[:200]}")
                    continue

                await self._handle_packet(packet)

        except asyncio.CancelledError:
            logger.debug("Stdout reader cancelled")
        except Exception as e:
            logger.error(f"Stdout reader error: {e}")
        finally:
            # If we're not intentionally closed, attempt reconnection
            if not self._closed and self._state != BridgeState.STOPPED:
                logger.info("Attempting reconnection after stdout close...")
                self._state = BridgeState.RECONNECTING
                asyncio.create_task(self._auto_reconnect())

    async def _read_stderr(self) -> None:
        """Read and log Node.js stderr output."""
        try:
            while not self._closed and self._process and self._process.stderr:
                line_bytes = await self._process.stderr.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8").strip()
                if line:
                    logger.debug(f"[Node.js stderr] {line}")
        except (asyncio.CancelledError, Exception):
            pass

    async def _handle_packet(self, packet: dict) -> None:
        """Route a JSON packet from Node.js to the appropriate handler."""
        packet_type = packet.get("type", "unknown")

        # Resolve pending sends
        msg_id = packet.get("message_id") or packet.get("_cmd_id")
        if msg_id and msg_id in self._pending_sends:
            fut = self._pending_sends.pop(msg_id)
            if not fut.done():
                fut.set_result(packet)
            # Don't return — also dispatch to callbacks

        handler_map = {
            "qr": self._handle_qr,
            "qr_expired": self._handle_qr_expired,
            "connected": self._handle_connected,
            "disconnected": self._handle_disconnected,
            "reconnecting": self._handle_reconnecting,
            "message": self._handle_message,
            "message_sent": self._handle_message_sent,
            "send_error": self._handle_send_error,
            "error": self._handle_error,
            "status": self._handle_status,
            "group_participants_update": self._handle_group_participants,
            "presence_update": self._handle_presence,
            "creds_update": self._handle_creds_update,
            "unknown_command": lambda p: logger.warning(f"Unknown command response: {p}"),
        }

        handler = handler_map.get(packet_type)
        if handler:
            try:
                await handler(packet)
            except Exception as e:
                logger.error(f"Error in handler for {packet_type}: {e}")
        else:
            logger.warning(f"Unknown packet type: {packet_type}")

    # ── Packet Handlers ────────────────────────────────────────────

    async def _handle_qr(self, packet: dict) -> None:
        qr = packet.get("qr", "")
        self._state = BridgeState.WAITING_QR
        logger.info("QR code received")
        if self.on_qr:
            try:
                self.on_qr(qr)
            except Exception as e:
                logger.error(f"on_qr callback error: {e}")

    async def _handle_qr_expired(self, packet: dict) -> None:
        logger.info("QR code expired")
        if self.on_qr_expired:
            try:
                self.on_qr_expired()
            except Exception as e:
                logger.error(f"on_qr_expired callback error: {e}")

    async def _handle_connected(self, packet: dict) -> None:
        self._state = BridgeState.CONNECTED
        self._reconnect_count = 0
        self._phone_number = packet.get("phone_number")
        self._phone_name = packet.get("phone_name")
        logger.info(f"Connected as {self._phone_name} ({self._phone_number})")
        if self.on_connected:
            try:
                self.on_connected(packet)
            except Exception as e:
                logger.error(f"on_connected callback error: {e}")

    async def _handle_disconnected(self, packet: dict) -> None:
        reason = packet.get("reason", "unknown")
        status_code = packet.get("statusCode")
        logger.info(f"Disconnected: {reason} (code: {status_code})")

        if reason == "logged_out":
            self._state = BridgeState.DISCONNECTED
        elif reason == "manual":
            self._state = BridgeState.STOPPED
        else:
            self._state = BridgeState.DISCONNECTED

        if self.on_disconnected:
            try:
                self.on_disconnected(packet)
            except Exception as e:
                logger.error(f"on_disconnected callback error: {e}")

    async def _handle_reconnecting(self, packet: dict) -> None:
        self._state = BridgeState.RECONNECTING
        attempt = packet.get("attempt", 0)
        delay = packet.get("delay", 0)
        logger.info(f"Reconnecting (attempt {attempt}, delay {delay}ms)")
        if self.on_reconnecting:
            try:
                self.on_reconnecting(packet)
            except Exception as e:
                logger.error(f"on_reconnecting callback error: {e}")

    async def _handle_message(self, packet: dict) -> None:
        data = packet.get("data", {})
        logger.debug(f"Message from {data.get('sender')}: {data.get('content', '')[:80]}")
        if self.on_message:
            try:
                self.on_message(data)
            except Exception as e:
                logger.error(f"on_message callback error: {e}")

    async def _handle_message_sent(self, packet: dict) -> None:
        logger.debug(f"Message sent: {packet.get('wa_message_id')}")
        if self.on_message_sent:
            try:
                self.on_message_sent(packet)
            except Exception as e:
                logger.error(f"on_message_sent callback error: {e}")

    async def _handle_send_error(self, packet: dict) -> None:
        logger.error(f"Send error: {packet.get('error')}")
        if self.on_send_error:
            try:
                self.on_send_error(packet)
            except Exception as e:
                logger.error(f"on_send_error callback error: {e}")

    async def _handle_error(self, packet: dict) -> None:
        message = packet.get("message", "Unknown error")
        fatal = packet.get("fatal", False)
        logger.error(f"Node.js error: {message} (fatal={fatal})")
        if fatal:
            self._state = BridgeState.ERROR
        if self.on_error:
            try:
                self.on_error(packet)
            except Exception as e:
                logger.error(f"on_error callback error: {e}")

    async def _handle_status(self, packet: dict) -> None:
        logger.debug(f"Status: connected={packet.get('connected')}, phone={packet.get('phone_number')}")

    async def _handle_group_participants(self, packet: dict) -> None:
        if self.on_group_participants:
            try:
                self.on_group_participants(packet.get("data", {}))
            except Exception as e:
                logger.error(f"on_group_participants callback error: {e}")

    async def _handle_presence(self, packet: dict) -> None:
        if self.on_presence:
            try:
                self.on_presence(packet.get("data", {}))
            except Exception as e:
                logger.error(f"on_presence callback error: {e}")

    async def _handle_creds_update(self, packet: dict) -> None:
        logger.debug("Credentials updated")
        if self.on_creds_update:
            try:
                self.on_creds_update()
            except Exception as e:
                logger.error(f"on_creds_update callback error: {e}")

    async def _auto_reconnect(self) -> None:
        """Auto-reconnect with exponential backoff."""
        if self._closed or self._state == BridgeState.STOPPED:
            return

        self._reconnect_count += 1
        if self._reconnect_count > MAX_RECONNECT_TRIES:
            logger.error(f"Max reconnect tries ({MAX_RECONNECT_TRIES}) reached. Giving up.")
            self._state = BridgeState.ERROR
            return

        delay = min(
            INITIAL_RETRY_DELAY * (BACKOFF_MULTIPLIER ** (self._reconnect_count - 1)),
            MAX_RETRY_DELAY,
        )
        logger.info(f"Auto-reconnect in {delay:.0f}s (attempt {self._reconnect_count}/{MAX_RECONNECT_TRIES})")

        await asyncio.sleep(delay)

        if self._closed or self._state == BridgeState.STOPPED:
            return

        try:
            await self.start()
        except Exception as e:
            logger.error(f"Auto-reconnect failed: {e}")
            asyncio.create_task(self._auto_reconnect())
