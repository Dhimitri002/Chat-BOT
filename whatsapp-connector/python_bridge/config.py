"""
Python Bridge Configuration — Flora Platform
=============================================
Configuration for the Python bridge that communicates with the
Node.js WhatsApp connector via subprocess streams (stdin/stdout).

Environment variables:
    NODE_SCRIPT          — Path to the Node.js connector script
    SESSION_ID           — WhatsApp session identifier
    BOT_ID               — Bot identifier
    AUTH_DIR             — Authentication directory for Baileys
    LOG_LEVEL            — Log verbosity (debug/info/warning/error)
    WS_HOST              — WebSocket server host
    WS_PORT              — WebSocket server port
    BACKEND_URL          — FastAPI backend base URL
    HEARTBEAT_INTERVAL   — Node.js heartbeat check interval in seconds
    MAX_RECONNECT_TRIES  — Max auto-reconnect attempts
    CALLBACK_TIMEOUT     — Timeout for callbacks in seconds
    INITIAL_RETRY_DELAY  — Initial retry delay in seconds
    MAX_RETRY_DELAY      — Maximum retry delay in seconds
"""

import os
import sys
from pathlib import Path
from typing import Optional

# ── Paths ──────────────────────────────────────────────────────────────

# Project root (whatsapp-connector/)
PROJECT_ROOT = Path(__file__).parent.parent
NODE_SCRIPT = os.environ.get("NODE_SCRIPT", str(PROJECT_ROOT / "dist" / "index.js"))

# If dist doesn't exist, fall back to src
if not Path(NODE_SCRIPT).exists():
    NODE_SRC = PROJECT_ROOT / "src" / "index.js"
    if NODE_SRC.exists():
        NODE_SCRIPT = str(NODE_SRC)

AUTH_DIR = os.environ.get("AUTH_DIR", str(PROJECT_ROOT / ".wa_auth"))

# ── Session ────────────────────────────────────────────────────────────

BOT_ID = os.environ.get("BOT_ID", "default")
SESSION_ID = os.environ.get("SESSION_ID", "default")

# ── Logging ────────────────────────────────────────────────────────────

LOG_LEVEL = os.environ.get("LOG_LEVEL", "info")

# ── WebSocket Bridge ───────────────────────────────────────────────────

WS_HOST = os.environ.get("WS_HOST", "127.0.0.1")
WS_PORT = int(os.environ.get("WS_PORT", "3333"))
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# ── Connection ─────────────────────────────────────────────────────────

HEARTBEAT_INTERVAL = int(os.environ.get("HEARTBEAT_INTERVAL", "30"))
MAX_RECONNECT_TRIES = int(os.environ.get("MAX_RECONNECT_TRIES", "10"))
CALLBACK_TIMEOUT = int(os.environ.get("CALLBACK_TIMEOUT", "30"))

# Exponential backoff parameters
INITIAL_RETRY_DELAY = float(os.environ.get("INITIAL_RETRY_DELAY", "2"))
MAX_RETRY_DELAY = float(os.environ.get("MAX_RETRY_DELAY", "60"))
BACKOFF_MULTIPLIER = float(os.environ.get("BACKOFF_MULTIPLIER", "2"))

# Validate configuration
def validate():
    """Validate critical configuration paths and values."""
    errors = []

    if not Path(NODE_SCRIPT).exists():
        errors.append(f"Node script not found: {NODE_SCRIPT}")

    if not Path(AUTH_DIR).exists():
        try:
            Path(AUTH_DIR).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            errors.append(f"Cannot create auth dir {AUTH_DIR}: {e}")

    if WS_PORT < 1 or WS_PORT > 65535:
        errors.append(f"Invalid WS_PORT: {WS_PORT}")

    if MAX_RECONNECT_TRIES < 0:
        errors.append(f"Invalid MAX_RECONNECT_TRIES: {MAX_RECONNECT_TRIES}")

    if errors:
        for err in errors:
            print(f"[CONFIG ERROR] {err}", file=sys.stderr)
        return False

    return True
