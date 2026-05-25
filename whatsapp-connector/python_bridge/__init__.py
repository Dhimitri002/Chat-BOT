"""
WhatsApp Python Bridge Package — Flora Package
================================================
Provides the Bridge class and configuration for connecting
the Node.js Baileys WhatsApp connector to the Python backend.
"""

from .bridge import Bridge, BridgeState
from .config import (
    NODE_SCRIPT,
    BOT_ID,
    SESSION_ID,
    AUTH_DIR,
    LOG_LEVEL,
    WS_HOST,
    WS_PORT,
    BACKEND_URL,
    HEARTBEAT_INTERVAL,
    MAX_RECONNECT_TRIES,
    CALLBACK_TIMEOUT,
    INITIAL_RETRY_DELAY,
    MAX_RETRY_DELAY,
    BACKOFF_MULTIPLIER,
    validate,
)

__all__ = [
    "Bridge",
    "BridgeState",
    "NODE_SCRIPT",
    "BOT_ID",
    "SESSION_ID",
    "AUTH_DIR",
    "LOG_LEVEL",
    "WS_HOST",
    "WS_PORT",
    "BACKEND_URL",
    "HEARTBEAT_INTERVAL",
    "MAX_RECONNECT_TRIES",
    "CALLBACK_TIMEOUT",
    "INITIAL_RETRY_DELAY",
    "MAX_RETRY_DELAY",
    "BACKOFF_MULTIPLIER",
    "validate",
]
