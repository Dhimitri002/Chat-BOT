"""
WhatsApp Python Bridge — Entry Point
======================================
Run the bridge standalone for testing or as a service.

Usage:
    python -m python_bridge
    python -m python_bridge --bot-id mybot --session-id default

Environment variables (see config.py for full list):
    BOT_ID       — Bot identifier
    SESSION_ID   — Session identifier
    LOG_LEVEL    — Logging level (debug/info/warning/error)
"""

import argparse
import asyncio
import logging
import signal
import sys
from typing import Optional

from .bridge import Bridge, BridgeState
from .config import validate

# ── Logging Setup ──────────────────────────────────────────────────────

def setup_logging(level: str = "info") -> None:
    """Configure structured logging for the bridge."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


# ── Main Application ───────────────────────────────────────────────────

class BridgeApp:
    """Main application that runs the bridge with event callbacks."""

    def __init__(self, bot_id: str, session_id: str):
        self.bot_id = bot_id
        self.session_id = session_id
        self.bridge: Optional[Bridge] = None
        self._shutdown_event = asyncio.Event()

    async def run(self) -> None:
        """Run the bridge and wait for shutdown signal."""
        self.bridge = Bridge(
            bot_id=self.bot_id,
            session_id=self.session_id,
        )

        # Register callbacks
        self.bridge.on_qr = self._on_qr
        self.bridge.on_qr_expired = self._on_qr_expired
        self.bridge.on_connected = self._on_connected
        self.bridge.on_disconnected = self._on_disconnected
        self.bridge.on_reconnecting = self._on_reconnecting
        self.bridge.on_message = self._on_message
        self.bridge.on_error = self._on_error
        self.bridge.on_message_sent = self._on_message_sent
        self.bridge.on_send_error = self._on_send_error

        try:
            await self.bridge.start()
        except RuntimeError as e:
            logger.error(f"Failed to start bridge: {e}")
            sys.exit(1)

        # Wait for shutdown signal
        await self._shutdown_event.wait()

        # Graceful shutdown
        if self.bridge:
            await self.bridge.stop()

    def request_shutdown(self) -> None:
        """Request graceful shutdown."""
        self._shutdown_event.set()

    # ── Callbacks ───────────────────────────────────────────────────

    def _on_qr(self, qr: str) -> None:
        logger.info("=" * 50)
        logger.info("QR CODE RECEIVED — Scan with WhatsApp")
        logger.info(f"QR (first 60 chars): {qr[:60]}...")
        logger.info("=" * 50)

    def _on_qr_expired(self) -> None:
        logger.warning("QR code expired — waiting for new one...")

    def _on_connected(self, data: dict) -> None:
        phone = data.get("phone_number", "unknown")
        name = data.get("phone_name", "unknown")
        logger.info(f"CONNECTED as {name} ({phone})")

    def _on_disconnected(self, data: dict) -> None:
        reason = data.get("reason", "unknown")
        code = data.get("statusCode")
        logger.warning(f"DISCONNECTED: {reason} (code: {code})")

    def _on_reconnecting(self, data: dict) -> None:
        attempt = data.get("attempt", 0)
        delay = data.get("delay", 0)
        logger.info(f"RECONNECTING (attempt {attempt}, delay {delay}ms)")

    def _on_message(self, data: dict) -> None:
        sender = data.get("sender_name", data.get("sender", "?"))
        content = data.get("content", "")
        is_group = data.get("is_group", False)
        group_tag = " [GROUP]" if is_group else ""
        logger.info(f"MESSAGE from {sender}{group_tag}: {content[:100]}")

    def _on_error(self, data: dict) -> None:
        message = data.get("message", "Unknown error")
        fatal = data.get("fatal", False)
        level = logging.CRITICAL if fatal else logging.ERROR
        logger.log(level, f"ERROR: {message}")

    def _on_message_sent(self, data: dict) -> None:
        logger.info(f"MESSAGE SENT: id={data.get('wa_message_id')}")

    def _on_send_error(self, data: dict) -> None:
        logger.error(f"SEND ERROR: {data.get('error')}")


# ── CLI Entry Point ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Flora Platform — WhatsApp Python Bridge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m python_bridge
  python -m python_bridge --bot-id mybot --session-id default
  python -m python_bridge --log-level debug
        """,
    )
    parser.add_argument("--bot-id", default="default", help="Bot identifier")
    parser.add_argument("--session-id", default="default", help="Session identifier")
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging level",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)

    # Validate configuration
    if not validate():
        logger.error("Configuration validation failed")
        sys.exit(1)

    app = BridgeApp(bot_id=args.bot_id, session_id=args.session_id)

    # Handle signals
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _signal_handler():
        logger.info("Shutdown signal received")
        app.request_shutdown()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            signal.signal(sig, lambda s, f: _signal_handler())

    try:
        loop.run_until_complete(app.run())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")
    finally:
        loop.close()
        logger.info("Bridge application exited")


if __name__ == "__main__":
    main()
