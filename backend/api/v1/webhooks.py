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
import uuid
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
    4. Broadcasts via WebSocket
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

    # Store message in database
    try:
        await _store_incoming_message_in_db(message)
    except Exception as e:
        logger.error("Failed to store incoming message: %s", e)

    # Update conversation
    try:
        await _update_conversation_from_webhook(message)
    except Exception as e:
        logger.error("Failed to update conversation: %s", e)

    # Broadcast via WebSocket
    notifier = service._notifier
    if notifier and bot_id:
        await notifier.broadcast_message(bot_id, {
            "direction": "in",
            "id": message.id,
            "from": message.from_number,
            "text": message.text,
            "media_url": message.media_url,
            "media_type": message.media_type,
            "is_group": message.is_group,
            "push_name": message.push_name,
            "timestamp": message.timestamp.isoformat(),
        })

    # Dispatch to the Flora engine for AI response
    await _dispatch_to_flora_engine(message, service)


async def _store_incoming_message_in_db(message: IncomingMessage) -> None:
    """Store an incoming message in the database."""
    try:
        from backend.database import AsyncSessionLocal
        from backend.models.message import Message
        from sqlalchemy import insert

        async with AsyncSessionLocal() as db:
            await db.execute(
                insert(Message).values(
                    id=str(uuid.uuid4()),
                    bot_id=message.bot_id,
                    whatsapp_message_id=message.id,
                    direction="in",
                    sender_phone=message.from_number,
                    sender_name=message.push_name or "",
                    message_type=_map_webhook_message_type(message),
                    content=message.text or "",
                    media_url=message.media_url,
                    media_type=message.media_type,
                    media_caption=message.media_caption,
                    is_read=False,
                    is_delivered=True,
                    whatsapp_status="received",
                    raw_data=message.raw,
                )
            )
            await db.commit()
            logger.debug("Incoming message stored in DB: %s", message.id)
    except Exception as e:
        logger.error("Failed to store incoming message in DB: %s", e)


async def _update_conversation_from_webhook(message: IncomingMessage) -> None:
    """Update the conversation thread from an incoming webhook message."""
    try:
        from backend.database import AsyncSessionLocal
        from backend.models.conversation import Conversation
        from sqlalchemy import select, update

        text = message.text or message.media_caption or ""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Conversation).where(
                    Conversation.bot_id == message.bot_id,
                    Conversation.contact_phone == message.from_number,
                )
            )
            conversation = result.scalar_one_or_none()

            if conversation:
                await db.execute(
                    update(Conversation)
                    .where(Conversation.id == conversation.id)
                    .values(
                        last_message=text[:200],
                        last_message_at=datetime.now(timezone.utc),
                        unread_count=Conversation.unread_count + 1,
                        updated_at=datetime.now(timezone.utc),
                    )
                )
            else:
                db.add(Conversation(
                    id=str(uuid.uuid4()),
                    bot_id=message.bot_id,
                    contact_phone=message.from_number,
                    contact_name=message.push_name or "",
                    last_message=text[:200],
                    last_message_at=datetime.now(timezone.utc),
                    unread_count=1,
                ))
            await db.commit()
    except Exception as e:
        logger.error("Failed to update conversation from webhook: %s", e)


def _map_webhook_message_type(message: IncomingMessage) -> str:
    """Map webhook message to internal message type."""
    if message.media_type:
        return message.media_type
    return "text"


async def _handle_message_status(data: dict, service: WhatsAppService) -> None:
    """
    Process a message status update (sent, delivered, read, failed).

    Updates the Message record in the database with the delivery status.
    """
    message_id = data.get("messageId", "")
    message_status = data.get("status", "")  # sent, delivered, read, failed
    session_id = data.get("sessionId", "")
    recipient = data.get("to", "")

    logger.info(
        "Message %s status: %s (session %s, to=%s)",
        message_id, message_status, session_id, recipient,
    )

    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import update
        from backend.models.message import Message

        async with AsyncSessionLocal() as db:
            update_values = {
                "whatsapp_status": message_status,
            }
            if message_status == "sent":
                update_values["is_delivered"] = False
            elif message_status == "delivered":
                update_values["is_delivered"] = True
            elif message_status == "read":
                update_values["is_delivered"] = True
                update_values["is_read"] = True
            elif message_status == "failed":
                update_values["whatsapp_status"] = "failed"

            await db.execute(
                update(Message)
                .where(Message.whatsapp_message_id == message_id)
                .values(**update_values)
            )
            await db.commit()
            logger.debug("Message %s status updated to %s", message_id, message_status)
    except Exception as e:
        logger.error("Failed to update message status for %s: %s", message_id, e)

    # Notify via WebSocket
    conn = service.get_connection(session_id)
    if conn:
        notifier = service._notifier
        if notifier and conn.bot_id:
            await notifier.broadcast_message(conn.bot_id, {
                "direction": "status",
                "message_id": message_id,
                "status": message_status,
                "to": recipient,
            })

    # Log failures specially
    if message_status == "failed":
        error_info = data.get("error", "Unknown error")
        logger.error(
            "Message %s failed to deliver to %s: %s",
            message_id, recipient, error_info,
        )


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

    # Map connector states to our internal states
    state_mapping = {
        "connected": ConnectionState.CONNECTED,
        "disconnected": ConnectionState.DISCONNECTED,
        "qr": ConnectionState.QR_WAITING,
        "connecting": ConnectionState.CONNECTING,
        "error": ConnectionState.ERROR,
        "loggedOut": ConnectionState.LOGGED_OUT,
    }

    internal_state = state_mapping.get(new_state)
    if not internal_state:
        logger.warning("Unknown connection state: %s", new_state)
        return

    if new_state == "connected":
        await conn._set_state(ConnectionState.CONNECTED)
        conn._phone_number = data.get("phoneNumber", conn._phone_number)
        conn._push_name = data.get("pushName", conn._push_name)
        conn._reconnect_policy.reset()
        # Save metadata
        conn._store.save_metadata(session_id, {
            "phone_number": conn._phone_number,
            "push_name": conn._push_name,
            "connected_at": datetime.now(timezone.utc).isoformat(),
        })
        # Clear QR data
        conn._qr_string = None
        conn._qr_expires = None
    elif new_state == "disconnected":
        reason = data.get("reason", "unknown")
        if reason == "loggedOut":
            await conn._set_state(ConnectionState.LOGGED_OUT)
            conn._store.delete_session(session_id)
        else:
            await conn._set_state(ConnectionState.DISCONNECTED)
            # Auto-reconnect for non-logout disconnections
            asyncio.create_task(conn._handle_auto_reconnect())
    elif new_state == "qr":
        qr_string = data.get("qr", "")
        if qr_string:
            conn.update_qr(qr_string)
        await conn._set_state(ConnectionState.QR_WAITING)
    elif new_state == "connecting":
        await conn._set_state(ConnectionState.CONNECTING)
    elif new_state == "error":
        error_msg = data.get("error", "Unknown error")
        await conn._set_state(ConnectionState.ERROR, error_msg)
        logger.error("Connection error for session %s: %s", session_id, error_msg)
    elif new_state == "loggedOut":
        await conn._set_state(ConnectionState.LOGGED_OUT)
        conn._store.delete_session(session_id)

    # Broadcast status via WebSocket
    notifier = service._notifier
    if notifier and conn.bot_id:
        await notifier.broadcast_status(conn.bot_id, conn.status)


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

    This handler:
    1. Loads the bot configuration
    2. Sends the message through the chat engine (commands -> intents -> LLM)
    3. Sends the response back via WhatsApp
    4. Broadcasts the response via WebSocket
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

            if not msg_text:
                logger.debug("Empty message text, skipping AI processing")
                return

            # Process through the chat engine
            from backend.core.chat_engine import ChatEngine
            engine = ChatEngine(db, bot)
            response = await engine.process_message(
                message=msg_text,
                session_id=message.from_number,
            )

            if response and response.get("content"):
                response_text = response["content"]
                # Send the response back via WhatsApp
                conn = service.get_connection(message.session_id)
                if conn and conn.state == ConnectionState.CONNECTED:
                    result = await conn.send_text(
                        to=message.from_number,
                        text=response_text,
                        reply_to=message.id if not message.is_group else None,
                    )
                    if result.success:
                        logger.info(
                            "AI response sent to %s (msg_id: %s)",
                            message.from_number, result.message_id,
                        )
                        # Broadcast outgoing message via WebSocket
                        notifier = service._notifier
                        if notifier and message.bot_id:
                            await notifier.broadcast_message(message.bot_id, {
                                "direction": "out",
                                "id": result.message_id,
                                "to": message.from_number,
                                "text": response_text,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            })
                    else:
                        logger.warning(
                            "Failed to send AI response to %s: %s",
                            message.from_number, result.error,
                        )
            else:
                logger.debug("Empty response from chat engine for bot %s", message.bot_id)

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
                    await conn._set_state(ConnectionState.QR_WAITING)
                    # Broadcast new QR via WebSocket
                    notifier = service._notifier
                    if notifier and conn.bot_id:
                        qr_data = conn.generate_qr()
                        await notifier.broadcast_qr(
                            conn.bot_id, qr_data.qr_code, qr_data.qr_string, qr_data.expires_at
                        )
                logger.info("QR code updated via webhook for session %s", session_id)

        elif event_type == "group":
            logger.info("Group event for session %s: %s", session_id, data.get("action", "unknown"))

        else:
            logger.warning("Unknown webhook event type: %s", event_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing webhook event %s: %s", event_type, e)

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
    msg_status = data.get("status", "")
    session_id = data.get("sessionId", "")
    recipient = data.get("to", "")
    timestamp = data.get("timestamp", time.time())

    logger.info(
        "Delivery status: message=%s status=%s to=%s session=%s",
        message_id, msg_status, recipient, session_id,
    )

    # Record delivery status in database (using async session)
    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import update
        from backend.models.message import Message

        async with AsyncSessionLocal() as db:
            update_values = {"whatsapp_status": msg_status}
            if msg_status == "sent":
                update_values["is_delivered"] = False
            elif msg_status == "delivered":
                update_values["is_delivered"] = True
            elif msg_status == "read":
                update_values["is_delivered"] = True
                update_values["is_read"] = True
            elif msg_status == "failed":
                update_values["whatsapp_status"] = "failed"

            await db.execute(
                update(Message)
                .where(Message.whatsapp_message_id == message_id)
                .values(**update_values)
            )
            await db.commit()
    except Exception as e:
        logger.warning("Failed to update delivery status for %s: %s", message_id, e)

    # Broadcast delivery status via WebSocket
    service = await WhatsAppService.get_instance()
    conn = service.get_connection(session_id)
    if conn:
        notifier = service._notifier
        if notifier and conn.bot_id:
            await notifier.broadcast_message(conn.bot_id, {
                "direction": "status",
                "message_id": message_id,
                "status": msg_status,
                "to": recipient,
            })

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
