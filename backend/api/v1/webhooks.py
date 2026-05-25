"""
Flora Platform — WhatsApp Webhooks Handler
===========================================
Handles incoming events from the WhatsApp connector service:
- Incoming messages (text, media, location, contacts)
- Message status updates (sent, delivered, read)
- Connection state changes (connected, disconnected, QR refresh)
- Group events (join, leave, update)

All webhook endpoints validate signatures for security.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request, status

from backend.config import settings
from backend.services.whatsapp_service import (
    WhatsAppService,
    ConnectionState,
    IncomingMessage,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["WebHooks"])

# ─── Signature Validation ───────────────────────────────────────────

def _validate_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Validate HMAC-SHA256 signature of webhook payload.

    The connector signs each webhook request with the shared secret.
    We verify by computing the expected signature and comparing securely.
    """
    if not secret or not signature:
        return False

    expected = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Use hmac.compare_digest to prevent timing attacks
    return hmac.compare_digest(expected, signature)


async def _validate_webhook_request(request: Request) -> dict:
    """
    Validate and parse an incoming webhook request.

    Returns the parsed JSON body if valid, raises HTTPException otherwise.
    """
    body = await request.body()

    # Validate signature
    signature = request.headers.get("X-Webhook-Signature", "")
    secret = settings.WHATSAPP_WEBHOOK_SECRET

    if not secret:
        logger.warning("WHATSAPP_WEBHOOK_SECRET not configured — webhook validation disabled")
    elif not _validate_signature(body, signature, secret):
        logger.warning(
            "Invalid webhook signature from %s (sig: %s...)",
            request.client.host if request.client else "unknown",
            signature[:20] if signature else "none",
        )
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Validate timestamp (reject events older than 5 minutes)
    timestamp_header = request.headers.get("X-Webhook-Timestamp", "")
    if timestamp_header:
        try:
            event_time = int(timestamp_header)
            if abs(time.time() - event_time) > 300:
                raise HTTPException(status_code=400, detail="Webhook timestamp too old")
        except ValueError:
            pass  # If not a valid timestamp, skip this check

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    return data


# ─── Event Handlers ─────────────────────────────────────────────────

async def _handle_incoming_message(data: dict, service: WhatsAppService) -> None:
    """
    Process an incoming message event.

    This is the core message handler that:
    1. Parses the incoming message
    2. Routes it to the appropriate bot session
    3. Dispatches to the Flora engine for AI response
    """
    session_id = data.get("sessionId", "")
    bot_id = data.get("botId", "")

    logger.info(
        "Incoming message for session %s: from=%s has_media=%s",
        session_id,
        data.get("from", "unknown"),
        bool(data.get("mediaUrl")),
    )

    if not session_id:
        logger.error("Incoming message has no session_id")
        return

    # Build the incoming message model
    try:
        message = IncomingMessage(
            id=data.get("id", ""),
            from_number=data.get("from", ""),
            to_number=data.get("to", ""),
            text=data.get("text"),
            media_url=data.get("mediaUrl"),
            media_type=data.get("mediaType"),
            media_caption=data.get("mediaCaption"),
            timestamp=datetime.fromtimestamp(
                data.get("timestamp", time.time()), tz=timezone.utc
            ),
            is_group=data.get("isGroup", False),
            group_id=data.get("groupId"),
            push_name=data.get("pushName"),
            session_id=session_id,
            bot_id=bot_id,
            raw=data,
        )
    except Exception as e:
        logger.error("Failed to parse incoming message: %s", e)
        return

    # Dispatch to the Flora engine for AI response
    await _dispatch_to_flora_engine(message, service)


async def _handle_message_status(data: dict, service: WhatsAppService) -> None:
    """
    Process a message status update (sent, delivered, read, failed).
    """
    message_id = data.get("messageId", "")
    message_status = data.get("status", "")  # sent, delivered, read, failed
    session_id = data.get("sessionId", "")

    logger.info(
        "Message %s status: %s (session %s)", message_id, message_status, session_id
    )

    # Update delivery status in database
    if message_status == "failed":
        error_info = data.get("error", "Unknown error")
        logger.error("Message %s failed to deliver: %s", message_id, error_info)


async def _handle_connection_update(data: dict, service: WhatsAppService) -> None:
    """
    Process a connection state update from the connector.
    """
    session_id = data.get("sessionId", "")
    new_state = data.get("state", "")

    logger.info("Connection update for session %s: %s", session_id, new_state)

    conn = service.get_connection(session_id)
    if not conn:
        logger.warning("Connection update for unknown session %s", session_id)
        return

    if new_state == "connected":
        conn.state = ConnectionState.CONNECTED
        conn._phone_number = data.get("phoneNumber", conn._phone_number)
        conn._push_name = data.get("pushName", conn._push_name)
        conn._connected_at = datetime.now(timezone.utc)
        conn._reconnect_policy.reset()
    elif new_state == "disconnected":
        reason = data.get("reason", "unknown")
        if reason == "loggedOut":
            conn.state = ConnectionState.LOGGED_OUT
            conn._store.delete_session(session_id)
        else:
            conn.state = ConnectionState.DISCONNECTED
    elif new_state == "qr":
        qr_string = data.get("qr", "")
        if qr_string:
            conn.update_qr(qr_string)
            conn.state = ConnectionState.QR_WAITING
    elif new_state == "connecting":
        conn.state = ConnectionState.CONNECTING
    elif new_state == "error":
        conn.state = ConnectionState.ERROR
        logger.error("Connection error for session %s: %s", session_id, data.get("error", ""))


async def _handle_auth_state(data: dict, service: WhatsAppService) -> None:
    """
    Save updated authentication state from the connector.
    Called periodically to persist session credentials.
    """
    session_id = data.get("sessionId", "")
    auth_state = data.get("state", {})

    if session_id and auth_state:
        conn = service.get_connection(session_id)
        if conn:
            conn._store.save_auth_state(session_id, auth_state)
            logger.debug("Auth state saved for session %s", session_id)


async def _dispatch_to_flora_engine(message: IncomingMessage, service: WhatsAppService) -> None:
    """
    Dispatch an incoming message to the Flora AI engine for processing.

    This is a fire-and-forget dispatch that:
    1. Loads the bot configuration
    2. Sends the message through the chat engine (commands -> intents -> LLM)
    3. Sends the response back via WhatsApp
    """
    try:
        from backend.database import AsyncSessionLocal
        from backend.models.bot import Bot
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            # Load the bot
            result = await db.execute(select(Bot).where(Bot.id == message.bot_id))
            bot = result.scalar_one_or_none()

            if not bot:
                logger.warning("Bot %s not found for incoming message", message.bot_id)
                return

            if not bot.is_active:
                logger.debug("Bot %s is not active, ignoring message", message.bot_id)
                return

            # Build the message text
            msg_text = message.text or message.media_caption or ""

            # Process through the chat engine
            from backend.core.chat_engine import ChatEngine
            engine = ChatEngine(db, bot)
            response = await engine.process_message(
                message=msg_text,
                session_id=message.from_number,  # Use phone number as session key
            )

            if response and response.get("content"):
                response_text = response["content"]
                # Send the response back through WhatsApp
                conn = service.get_connection(message.session_id)
                if conn and conn.state == ConnectionState.CONNECTED:
                    await conn.send_text(
                        to=message.from_number,
                        text=response_text,
                        reply_to=message.id,
                    )
                    logger.info("Sent AI response to %s", message.from_number)
            else:
                logger.warning("Empty response from chat engine for bot %s", message.bot_id)

    except Exception as e:
        logger.exception("Error dispatching message to Flora engine: %s", e)


# ─── Webhook Endpoints ──────────────────────────────────────────────

@router.post(
    "/whatsapp",
    status_code=status.HTTP_200_OK,
    summary="WhatsApp webhook receiver",
    description="Receives events from the WhatsApp connector: messages, status updates, connection changes.",
    response_model=dict,
)
async def whatsapp_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    x_webhook_timestamp: Optional[str] = Header(None, alias="X-Webhook-Timestamp"),
    x_event_type: Optional[str] = Header(None, alias="X-Event-Type"),
):
    """
    Main webhook endpoint for WhatsApp connector events.

    The connector sends events as POST requests with:
    - X-Webhook-Signature: HMAC-SHA256 signature of the body
    - X-Webhook-Timestamp: Unix timestamp of the event
    - X-Event-Type: Type of event (message, status, connection, auth)

    Supported event types:
    - message: Incoming message from a WhatsApp user
    - status: Message delivery status update
    - connection: Connection state change
    - auth: Authentication state update

    Returns 200 OK immediately after validating the signature.
    Events are processed asynchronously.
    """
    # Validate and parse the webhook request
    data = await _validate_webhook_request(request)

    # Get the event type from header or body
    event_type = x_event_type or data.get("event", "unknown")
    session_id = data.get("sessionId", "")

    logger.info(
        "Webhook received: event=%s session=%s from=%s",
        event_type,
        session_id,
        request.client.host if request.client else "unknown",
    )

    # Get the WhatsApp service
    service = await WhatsAppService.get_instance()

    # Route to appropriate handler (fire and forget for non-critical events)
    try:
        if event_type == "message":
            # Process messages synchronously to ensure delivery tracking
            await _handle_incoming_message(data, service)

        elif event_type == "status":
            asyncio.create_task(_handle_message_status(data, service))

        elif event_type == "connection":
            asyncio.create_task(_handle_connection_update(data, service))

        elif event_type == "auth":
            asyncio.create_task(_handle_auth_state(data, service))

        elif event_type == "qr":
            # QR code refresh event
            conn = service.get_connection(session_id)
            if conn:
                qr_string = data.get("qr", "")
                if qr_string:
                    conn.update_qr(qr_string)
                logger.info("QR code updated via webhook for session %s", session_id)

        elif event_type == "group":
            # Group event (join, leave, update)
            logger.info("Group event for session %s: %s", session_id, data.get("action", "unknown"))

        else:
            logger.warning("Unknown webhook event type: %s", event_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing webhook event %s: %s", event_type, e)
        # Return 200 to prevent the connector from retrying for non-retryable errors
        # The connector should have its own retry logic for critical failures

    return {"success": True, "message": "ok"}


@router.get(
    "/whatsapp",
    status_code=status.HTTP_200_OK,
    summary="WhatsApp webhook verification",
    description="Webhook verification endpoint for GET challenges from the connector.",
)
async def whatsapp_webhook_verify(
    request: Request,
):
    """
    Handle webhook verification (GET request).

    Some connectors send a GET request to verify the webhook URL.
    This endpoint responds with the challenge token.
    """
    hub_mode = request.query_params.get("hub.mode", "")
    hub_challenge = request.query_params.get("hub.challenge", "")
    hub_verify_token = request.query_params.get("hub.verify_token", "")

    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_WEBHOOK_SECRET:
        logger.info("Webhook verification successful")
        return {"challenge": hub_challenge}

    # Also support simple health check on this endpoint
    if not hub_mode:
        return {"status": "ok", "service": "whatsapp-webhook"}

    logger.warning("Webhook verification failed: invalid token")
    raise HTTPException(status_code=403, detail="Verification failed")


# ─── Outbound Delivery Status Webhook ───────────────────────────────

@router.post(
    "/delivery",
    status_code=status.HTTP_200_OK,
    summary="Delivery status webhook",
    description="Receives delivery status updates for sent messages.",
)
async def delivery_status_webhook(
    request: Request,
):
    """
    Handle delivery status callbacks.

    Tracks message delivery status:
    - sent: Message was sent to the server
    - delivered: Message was delivered to the recipient's device
    - read: Message was read by the recipient
    - failed: Message delivery failed
    """
    data = await _validate_webhook_request(request)

    message_id = data.get("messageId", "")
    status = data.get("status", "")
    session_id = data.get("sessionId", "")
    recipient = data.get("to", "")
    timestamp = data.get("timestamp", time.time())

    logger.info(
        "Delivery status: message=%s status=%s to=%s session=%s",
        message_id, status, recipient, session_id,
    )

    # Record delivery status in database
    try:
        from backend.database import SessionLocal
        from sqlalchemy import update
        from backend.models.message import Message

        async with SessionLocal() as db:
            await db.execute(
                update(Message)
                .where(Message.whatsapp_message_id == message_id)
                .values(
                    is_read=(status == "read"),
                )
            )
            await db.commit()
    except Exception as e:
        logger.warning("Failed to update delivery status for %s: %s", message_id, e)

    return {"success": True}


# ─── Connector-to-Bridge Webhook (Internal) ─────────────────────────

@router.post(
    "/internal/connector",
    status_code=status.HTTP_200_OK,
    summary="Internal connector bridge",
    description="Internal endpoint for the connector to push events directly.",
)
async def connector_bridge(
    request: Request,
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
):
    """
    Internal webhook for direct connector-to-API communication.

    This endpoint is used when the connector runs in the same network
    and can push events directly instead of through an external webhook.
    Protected by an internal token.
    """
    # Validate internal token
    internal_token = settings.WHATSAPP_CONNECTOR_TOKEN or settings.SECRET_KEY
    if not x_internal_token or x_internal_token != internal_token:
        raise HTTPException(status_code=401, detail="Invalid internal token")

    try:
        data = await request.body()
        event = json.loads(data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event.get("event", "")
    service = await WhatsAppService.get_instance()

    if event_type == "message":
        await _handle_incoming_message(event, service)
    elif event_type == "status":
        await _handle_message_status(event, service)
    elif event_type == "connection":
        await _handle_connection_update(event, service)
    elif event_type == "auth":
        await _handle_auth_state(event, service)

    return {"success": True}
