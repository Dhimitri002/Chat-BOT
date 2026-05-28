"""
Flora Platform — WhatsApp API Endpoints
========================================
REST API for managing WhatsApp connections, sending messages,
and monitoring session status.

All endpoints require authentication via JWT.
Session-scoped endpoints check that the user owns the bot.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db, require_role
from backend.services.whatsapp_service import (
    WhatsAppService,
    ConnectionState,
    OutgoingMessage,
    WebSocketNotifier,
)
from backend.schemas.whatsapp import (
    ConnectRequest,
    ConnectResponse,
    DisconnectRequest,
    DisconnectResponse,
    StatusResponse,
    SendMessageRequest,
    SendMessageResponse,
    QrResponse,
    RefreshQrResponse,
    SessionsResponse,
    SessionInfo,
    HealthCheckResponse,
    WebhookIncomingPayload,
    WebhookResponse,
    ChatHistoryResponse,
    ChatMessage,
    EventLogResponse,
    EventLogEntry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


async def _get_whatsapp_service() -> WhatsAppService:
    """Dependency to get the WhatsApp service singleton."""
    return await WhatsAppService.get_instance()


# ─── WebSocket for Real-Time Updates ────────────────────────────────

@router.websocket("/ws/{bot_id}")
async def whatsapp_websocket(
    websocket: WebSocket,
    bot_id: str,
):
    """
    WebSocket endpoint for real-time WhatsApp updates for a specific bot.

    Events pushed to connected clients:
    - connection_status: Connection state changes (connecting, connected, disconnected, error)
    - qr_code: New QR code generated (with base64 image and expiry)
    - message: Incoming and outgoing messages

    Authentication: The client sends a JWT token as a query parameter:
    ws://host/api/v1/whatsapp/ws/{bot_id}?token=JWT_TOKEN
    """
    wa_service = await WhatsAppService.get_instance()
    notifier = wa_service._notifier

    if not notifier:
        await websocket.close(code=4001, reason="WebSocket notifier not initialized")
        return

    # Authenticate via query parameter token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    # Validate the token
    try:
        from jose import jwt, JWTError
        from backend.config import settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return

        # Check that the user owns the bot or is admin
        from sqlalchemy import select
        from backend.models import Bot
        from backend.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Bot).where(Bot.id == bot_id))
            bot = result.scalar_one_or_none()

        if not bot:
            await websocket.close(code=4004, reason="Bot not found")
            return

        # Role check: admin can connect to any bot
        user_role = payload.get("role", "user")
        if str(bot.owner_id) != str(user_id) and user_role != "admin":
            await websocket.close(code=4003, reason="Not authorized for this bot")
            return

    except Exception as e:
        logger.warning("WebSocket auth failed: %s", e)
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await websocket.accept()
    await notifier.register(websocket, bot_id)

    # Send initial status
    conn = wa_service.get_connection_by_bot(bot_id)
    if conn:
        await notifier.broadcast_status(bot_id, conn.status)

    try:
        # Keep the connection alive and handle client messages
        # Client can send "ping" to keep alive, or "refresh_status"
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60.0,
                )
                msg_type = data.get("type", "")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})

                elif msg_type == "refresh_status":
                    if conn:
                        await notifier.broadcast_status(bot_id, conn.status)

                elif msg_type == "get_qr":
                    if conn and conn.state == ConnectionState.QR_WAITING:
                        try:
                            qr = conn.generate_qr()
                            await notifier.broadcast_qr(bot_id, qr.qr_code, qr.qr_string, qr.expires_at)
                        except ValueError as e:
                            await websocket.send_json({"type": "error", "message": str(e)})

                elif msg_type == "send_message":
                    # Send a message via WebSocket
                    if not conn or conn.state != ConnectionState.CONNECTED:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Session not connected",
                        })
                        continue
                    to = data.get("to", "")
                    text = data.get("text", "")
                    if not to or not text:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Missing 'to' or 'text'",
                        })
                        continue
                    result = await conn.send_text(to, text)
                    await websocket.send_json({
                        "type": "send_result",
                        "data": {
                            "success": result.success,
                            "message_id": result.message_id,
                            "error": result.error,
                        },
                    })

            except asyncio.TimeoutError:
                # Send a ping to keep the connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for bot %s", bot_id)
    except Exception as e:
        logger.error("WebSocket error for bot %s: %s", bot_id, e)
    finally:
        await notifier.unregister(websocket, bot_id)


# Global WebSocket endpoint (admin dashboard)
@router.websocket("/ws")
async def whatsapp_global_websocket(
    websocket: WebSocket,
):
    """
    Global WebSocket endpoint for the admin dashboard.
    Broadcasts all WhatsApp events (all bots).

    ws://host/api/v1/whatsapp/ws?token=ADMIN_JWT_TOKEN
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        from jose import jwt, JWTError
        from backend.config import settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("role") != "admin":
            await websocket.close(code=4003, reason="Admin access required")
            return
    except Exception:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    wa_service = await WhatsAppService.get_instance()
    notifier = wa_service._notifier
    if not notifier:
        await websocket.close(code=4001, reason="Notifier not initialized")
        return

    await websocket.accept()
    await notifier.register(websocket)  # No bot_id = global listener

    # Send initial full status
    for session_status in wa_service.list_sessions():
        await notifier.broadcast_status(session_status.bot_id, session_status)

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("type") == "get_stats":
                    stats = await wa_service.get_service_stats()
                    await websocket.send_json({"type": "service_stats", "data": stats})
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        logger.info("Global WebSocket disconnected")
    except Exception as e:
        logger.error("Global WebSocket error: %s", e)
    finally:
        await notifier.unregister(websocket)


# ─── Connect ────────────────────────────────────────────────────────

@router.post(
    "/connect",
    response_model=ConnectResponse,
    status_code=status.HTTP_200_OK,
    summary="Connect a WhatsApp session",
    description="Creates a new WhatsApp connection for the specified bot. Returns a QR code to scan if authentication is needed, or connects immediately if a session already exists.",
)
async def connect_whatsapp(
    request: ConnectRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """
    Connect a bot to WhatsApp.

    Flow:
    1. Validates the bot exists and belongs to the current user (or user is admin)
    2. Creates or restores a WhatsApp session
    3. Returns QR code for scanning, or status if already connected
    """
    from sqlalchemy import select
    from backend.models import Bot

    result = await db.execute(select(Bot).where(Bot.id == request.bot_id))
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    if str(bot.owner_id) != str(current_user.id):
        await require_role("admin")(current_user)

    # Check rate limit: max 3 active sessions per user
    user_sessions = [
        s for s in wa_service.list_sessions()
        if s.state in (ConnectionState.CONNECTED, ConnectionState.QR_WAITING, ConnectionState.CONNECTING)
    ]
    if len(user_sessions) >= 3:
        raise HTTPException(
            status_code=429,
            detail="Maximum active sessions limit reached (3). Disconnect an existing session first.",
        )

    try:
        qr_data = await wa_service.create_session(
            bot_id=request.bot_id,
            session_id=request.session_id,
            phone_number=request.phone_number,
            webhook_url=request.webhook_url,
        )

        if qr_data:
            # QR code generated - user needs to scan
            return ConnectResponse(
                success=True,
                session_id=qr_data.session_id,
                state=ConnectionState.QR_WAITING,
                qr_code=qr_data.qr_code,
                qr_expires_at=qr_data.expires_at,
                message="Scan the QR code with your WhatsApp app to connect.",
            )

        # Session was restored/connected immediately
        conn = wa_service.get_connection_by_bot(request.bot_id)
        if conn and conn.state == ConnectionState.CONNECTED:
            return ConnectResponse(
                success=True,
                session_id=conn.session_id,
                state=ConnectionState.CONNECTED,
                message="Session restored and connected.",
            )

        # Fallback - should not reach here
        raise HTTPException(status_code=500, detail="Unexpected connection state")

    except ConnectionError as e:
        logger.error("Connection error for bot %s: %s", request.bot_id, e)
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error connecting bot %s: %s", request.bot_id, e)
        raise HTTPException(status_code=500, detail="Internal connection error")


# ─── Disconnect ─────────────────────────────────────────────────────

@router.post(
    "/disconnect",
    response_model=DisconnectResponse,
    status_code=status.HTTP_200_OK,
    summary="Disconnect a WhatsApp session",
)
async def disconnect_whatsapp(
    request: DisconnectRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """
    Disconnect a WhatsApp session.

    If session_id is provided, disconnects that specific session.
    If bot_id is provided, disconnects the bot's active session.
    Optionally removes stored session data (remove_data=true).
    """
    session_id = request.session_id

    # If bot_id provided, look up the session
    if not session_id and request.bot_id:
        from sqlalchemy import select
        from backend.models import Bot

        result = await db.execute(select(Bot).where(Bot.id == request.bot_id))
        bot = result.scalar_one_or_none()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        if str(bot.owner_id) != str(current_user.id):
            await require_role("admin")(current_user)

        conn = wa_service.get_connection_by_bot(request.bot_id)
        if conn:
            session_id = conn.session_id

    if not session_id:
        raise HTTPException(
            status_code=400,
            detail="Provide either session_id or bot_id",
        )

    conn = wa_service.get_connection(session_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify ownership via bot
    if conn.bot_id:
        from sqlalchemy import select
        from backend.models import Bot
        result = await db.execute(select(Bot).where(Bot.id == conn.bot_id))
        bot = result.scalar_one_or_none()
        if bot and str(bot.owner_id) != str(current_user.id):
            await require_role("admin")(current_user)

    try:
        disconnected = await wa_service.disconnect(session_id)
        if not disconnected:
            raise HTTPException(status_code=404, detail="Session not active")

        # Optionally remove stored data
        if request.remove_data:
            store = wa_service._store
            store.delete_session(session_id)

        return DisconnectResponse(
            success=True,
            session_id=session_id,
            message="Session disconnected successfully.",
        )
    except Exception as e:
        logger.exception("Error disconnecting session %s: %s", session_id, e)
        raise HTTPException(status_code=500, detail="Error disconnecting session")


# ─── Status ─────────────────────────────────────────────────────────

@router.get(
    "/status/{session_id}",
    response_model=StatusResponse,
    summary="Get connection status",
)
async def get_session_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """Get the full connection status of a WhatsApp session."""
    conn = wa_service.get_connection(session_id)
    if not conn:
        # Check if session has stored auth data
        stored = wa_service.list_stored_sessions()
        if session_id in stored:
            return StatusResponse(
                session_id=session_id,
                state=ConnectionState.DISCONNECTED,
                message="Session exists but is not currently active.",
            )
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify ownership
    if conn.bot_id:
        from sqlalchemy import select
        from backend.models import Bot
        result = await db.execute(select(Bot).where(Bot.id == conn.bot_id))
        bot = result.scalar_one_or_none()
        if bot and str(bot.owner_id) != str(current_user.id):
            await require_role("admin")(current_user)

    status_data = conn.status
    is_healthy = status_data.state == ConnectionState.CONNECTED
    is_qr_valid = (
        status_data.state == ConnectionState.QR_WAITING
        and status_data.qr_code is not None
        and status_data.qr_code != "expired"
    )

    return StatusResponse(
        session_id=status_data.session_id,
        bot_id=status_data.bot_id,
        state=status_data.state,
        phone_number=status_data.phone_number,
        push_name=status_data.push_name,
        battery_level=status_data.battery_level,
        plugged_in=status_data.plugged_in,
        connected_at=status_data.connected_at,
        last_seen=status_data.last_seen,
        retry_count=status_data.retry_count,
        qr_code=status_data.qr_code,
        is_healthy=is_healthy,
        is_qr_valid=is_qr_valid,
        message=_state_message(status_data.state),
    )


@router.get(
    "/status/bot/{bot_id}",
    response_model=StatusResponse,
    summary="Get connection status by bot ID",
)
async def get_bot_status(
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """Get the connection status for a bot's active WhatsApp session."""
    from sqlalchemy import select
    from backend.models import Bot

    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if str(bot.owner_id) != str(current_user.id):
        await require_role("admin")(current_user)

    conn = wa_service.get_connection_by_bot(bot_id)
    if not conn:
        # Check stored sessions
        stored = wa_service.list_stored_sessions()
        for sid in stored:
            meta = wa_service._store.load_metadata(sid)
            if meta and meta.get("bot_id") == bot_id:
                return StatusResponse(
                    session_id=sid,
                    bot_id=bot_id,
                    state=ConnectionState.DISCONNECTED,
                    message="Session exists but is not currently active.",
                )
        raise HTTPException(
            status_code=404,
            detail="No WhatsApp session found for this bot. Connect first.",
        )

    status_data = conn.status
    is_healthy = status_data.state == ConnectionState.CONNECTED
    is_qr_valid = (
        status_data.state == ConnectionState.QR_WAITING
        and status_data.qr_code is not None
        and status_data.qr_code != "expired"
    )

    return StatusResponse(
        session_id=status_data.session_id,
        bot_id=status_data.bot_id,
        state=status_data.state,
        phone_number=status_data.phone_number,
        push_name=status_data.push_name,
        battery_level=status_data.battery_level,
        plugged_in=status_data.plugged_in,
        connected_at=status_data.connected_at,
        last_seen=status_data.last_seen,
        retry_count=status_data.retry_count,
        qr_code=status_data.qr_code,
        is_healthy=is_healthy,
        is_qr_valid=is_qr_valid,
        message=_state_message(status_data.state),
    )


def _state_message(state: ConnectionState) -> str:
    """Return a human-readable message for the connection state."""
    messages = {
        ConnectionState.DISCONNECTED: "Session is disconnected.",
        ConnectionState.CONNECTING: "Session is connecting...",
        ConnectionState.QR_WAITING: "Waiting for QR code to be scanned.",
        ConnectionState.CONNECTED: "Session is connected and active.",
        ConnectionState.RECONNECTING: "Session is reconnecting...",
        ConnectionState.LOGGED_OUT: "Session was logged out. Scan QR again.",
        ConnectionState.ERROR: "Session encountered an error.",
    }
    return messages.get(state, f"Unknown state: {state}")


# ─── Send Message ───────────────────────────────────────────────────

@router.post(
    "/send",
    response_model=SendMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a WhatsApp message",
)
async def send_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """
    Send a message through a WhatsApp session.

    Supports text, media (image/video/audio/document), and button messages.
    The 'to' field should be a phone number in international format (digits only, no +).
    """
    # Verify session ownership
    conn = wa_service.get_connection(request.session_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Session not found")

    if conn.bot_id:
        from sqlalchemy import select
        from backend.models import Bot
        result = await db.execute(select(Bot).where(Bot.id == conn.bot_id))
        bot = result.scalar_one_or_none()
        if bot and str(bot.owner_id) != str(current_user.id):
            await require_role("admin")(current_user)

    # Build outgoing message
    msg = OutgoingMessage(
        to=request.to,
        text=request.text,
        media_url=request.media_url,
        media_type=request.media_type,
        media_caption=request.media_caption,
        media_filename=request.media_filename,
        buttons=request.buttons,
        reply_to=request.reply_to,
    )

    result = await wa_service.send_message(request.session_id, msg)

    if result.success:
        return SendMessageResponse(
            success=True,
            message_id=result.message_id,
            timestamp=result.timestamp,
            message="Message sent successfully.",
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=result.error or "Failed to send message",
        )


# ─── QR Code ────────────────────────────────────────────────────────

@router.get(
    "/qr/{session_id}",
    response_model=QrResponse,
    summary="Get current QR code",
)
async def get_qr_code(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """Get the current QR code for a session (if in QR_WAITING state)."""
    conn = wa_service.get_connection(session_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify ownership
    if conn.bot_id:
        from sqlalchemy import select
        from backend.models import Bot
        result = await db.execute(select(Bot).where(Bot.id == conn.bot_id))
        bot = result.scalar_one_or_none()
        if bot and str(bot.owner_id) != str(current_user.id):
            await require_role("admin")(current_user)

    if conn.state != ConnectionState.QR_WAITING:
        raise HTTPException(
            status_code=400,
            detail=f"Session is not in QR_WAITING state (current: {conn.state})",
        )

    try:
        qr_data = conn.generate_qr()
        return QrResponse(
            session_id=session_id,
            qr_code=qr_data.qr_code,
            qr_string=qr_data.qr_string,
            expires_at=qr_data.expires_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=410, detail=str(e))


@router.post(
    "/qr/{session_id}/refresh",
    response_model=RefreshQrResponse,
    summary="Refresh QR code",
)
async def refresh_qr_code(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """Request a fresh QR code for a session."""
    conn = wa_service.get_connection(session_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify ownership
    if conn.bot_id:
        from sqlalchemy import select
        from backend.models import Bot
        result = await db.execute(select(Bot).where(Bot.id == conn.bot_id))
        bot = result.scalar_one_or_none()
        if bot and str(bot.owner_id) != str(current_user.id):
            await require_role("admin")(current_user)

    try:
        qr_data = await wa_service.refresh_qr(session_id)
        return RefreshQrResponse(
            session_id=session_id,
            qr_code=qr_data.qr_code,
            qr_string=qr_data.qr_string,
            expires_at=qr_data.expires_at,
            message="New QR code generated. Scan with your WhatsApp app.",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ─── Sessions Listing ───────────────────────────────────────────────

@router.get(
    "/sessions",
    response_model=SessionsResponse,
    summary="List all active sessions",
)
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """
    List all active WhatsApp sessions.

    Admins see all sessions. Regular users see only their own.
    """
    is_admin = current_user.role == "admin"
    active_sessions = wa_service.list_sessions()
    stored_sessions = wa_service.list_stored_sessions()

    session_infos = []
    for s in active_sessions:
        # Filter by ownership for non-admins
        if not is_admin and s.bot_id:
            from sqlalchemy import select
            from backend.models import Bot
            result = await db.execute(select(Bot).where(Bot.id == s.bot_id))
            bot = result.scalar_one_or_none()
            if bot and str(bot.owner_id) != str(current_user.id):
                continue

        session_infos.append(SessionInfo(
            session_id=s.session_id,
            bot_id=s.bot_id,
            state=s.state,
            phone_number=s.phone_number,
            push_name=s.push_name,
            connected_at=s.connected_at,
            last_seen=s.last_seen,
        ))

    # Include stored but inactive sessions
    active_ids = {s.session_id for s in active_sessions}
    for sid in stored_sessions:
        if sid not in active_ids:
            meta = wa_service._store.load_metadata(sid)
            if meta:
                if not is_admin and meta.get("bot_id"):
                    from sqlalchemy import select
                    from backend.models import Bot
                    result = await db.execute(
                        select(Bot).where(Bot.id == meta["bot_id"])
                    )
                    bot = result.scalar_one_or_none()
                    if bot and str(bot.owner_id) != str(current_user.id):
                        continue

                session_infos.append(SessionInfo(
                    session_id=sid,
                    bot_id=meta.get("bot_id", ""),
                    state=ConnectionState.DISCONNECTED,
                    phone_number=meta.get("phone_number"),
                    push_name=meta.get("push_name"),
                ))

    return SessionsResponse(
        sessions=session_infos,
        total=len(session_infos),
    )


# ─── Health Check ───────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="WhatsApp service health check",
)
async def whatsapp_health(
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """Check if the WhatsApp service is running and healthy."""
    sessions = wa_service.list_sessions()
    active_count = sum(
        1 for s in sessions
        if s.state == ConnectionState.CONNECTED
    )
    qr_count = sum(
        1 for s in sessions
        if s.state == ConnectionState.QR_WAITING
    )
    error_count = sum(
        1 for s in sessions
        if s.state == ConnectionState.ERROR
    )

    return HealthCheckResponse(
        status="healthy" if active_count > 0 or len(sessions) == 0 else "degraded",
        active_sessions=active_count,
        qr_waiting=qr_count,
        errors=error_count,
        total_sessions=len(sessions),
        timestamp=datetime.now(timezone.utc),
    )


# ─── Connection Logs ────────────────────────────────────────────────

@router.get(
    "/logs/{session_id}",
    summary="Get connection logs",
)
async def get_connection_logs(
    session_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    event_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """Get connection event logs for debugging."""
    conn = wa_service.get_connection(session_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify ownership
    if conn.bot_id:
        from sqlalchemy import select
        from backend.models import Bot
        result = await db.execute(select(Bot).where(Bot.id == conn.bot_id))
        bot = result.scalar_one_or_none()
        if bot and str(bot.owner_id) != str(current_user.id):
            await require_role("admin")(current_user)

    logs = await wa_service.get_session_logs(session_id, limit=limit, event_type=event_type)
    return {"session_id": session_id, "logs": logs, "total": len(logs)}


# ─── Service Stats ──────────────────────────────────────────────────

@router.get(
    "/stats",
    summary="Get WhatsApp service statistics",
)
async def get_service_stats(
    current_user=Depends(get_current_user),
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """Get overall WhatsApp service statistics (admin only)."""
    await require_role("admin")(current_user)
    stats = await wa_service.get_service_stats()
    return stats


# ─── Webhook Endpoint (for external connectors) ─────────────────────

@router.post(
    "/webhook",
    response_model=WebhookResponse,
    summary="Receive webhook from external WhatsApp connector",
    description=(
        "Receives webhook events from an external WhatsApp connector or bridge service. "
        "Supports events: message, qr, connected, disconnected, state_change."
    ),
)
async def receive_webhook(
    payload: WebhookIncomingPayload,
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """
    Process incoming webhook from an external WhatsApp connector/bridge.

    This endpoint is called by external services (Baileys bridge, wppconnect-server,
    etc.) to deliver WhatsApp events to the Flora Platform.

    Supported event types:
    - `message` / `messages.upsert`: Incoming WhatsApp message
    - `qr`: New QR code generated
    - `connected` / `connection.open`: Session connected
    - `disconnected` / `connection.close`: Session disconnected
    - `state_change`: Connection state changed
    """
    try:
        result = await wa_service.process_incoming_webhook(payload.model_dump())
        if result.get("success"):
            return WebhookResponse(success=True, message=result.get("message", "ok"))
        return WebhookResponse(success=False, message=result.get("message", "error"))
    except Exception as e:
        logger.error("Webhook processing error: %s", e, exc_info=True)
        return WebhookResponse(success=False, message=f"Error: {str(e)}")


@router.post(
    "/webhook/{session_id}",
    response_model=WebhookResponse,
    summary="Receive webhook for a specific session",
)
async def receive_session_webhook(
    session_id: str,
    payload: WebhookIncomingPayload,
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """Webhook endpoint scoped to a specific session ID."""
    # Ensure the session_id from the path is used
    data = payload.model_dump()
    data["session_id"] = session_id
    try:
        result = await wa_service.process_incoming_webhook(data)
        if result.get("success"):
            return WebhookResponse(success=True, message=result.get("message", "ok"))
        return WebhookResponse(success=False, message=result.get("message", "error"))
    except Exception as e:
        logger.error("Webhook processing error for session %s: %s", session_id, e, exc_info=True)
        return WebhookResponse(success=False, message=f"Error: {str(e)}")


# ─── Chat History ───────────────────────────────────────────────────

@router.get(
    "/chat/{session_id}",
    response_model=ChatHistoryResponse,
    summary="Get chat history for a session",
)
async def get_chat_history(
    session_id: str,
    contact_phone: str = Query(default="", description="Filter by contact phone number"),
    limit: int = Query(default=50, ge=1, le=200),
    before_id: str = Query(default="", description="Get messages before this message ID"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """
    Get the chat history for a WhatsApp session.

    Optionally filter by contact phone number to get the conversation
    with a specific contact.
    """
    conn = wa_service.get_connection(session_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify ownership
    if conn.bot_id:
        from sqlalchemy import select
        from backend.models import Bot
        result = await db.execute(select(Bot).where(Bot.id == conn.bot_id))
        bot = result.scalar_one_or_none()
        if bot and str(bot.owner_id) != str(current_user.id):
            await require_role("admin")(current_user)

    messages = await wa_service.get_chat_history(
        session_id,
        contact_phone=contact_phone,
        limit=limit,
        before_id=before_id,
    )

    return ChatHistoryResponse(
        session_id=session_id,
        bot_id=conn.bot_id or "",
        contact_phone=contact_phone,
        messages=[
            ChatMessage(
                message_id=m.message_id,
                direction=m.direction,
                sender_phone=m.sender_phone,
                recipient_phone=m.recipient_phone,
                message_type=m.message_type,
                content=m.content,
                media_url=m.media_url,
                media_caption=m.media_caption,
                is_read=m.is_read,
                is_delivered=m.is_delivered,
                whatsapp_status=m.whatsapp_status,
                timestamp=m.timestamp,
                reply_to=m.reply_to,
            )
            for m in messages
        ],
        total=len(messages),
        has_more=len(messages) >= limit,
    )


# ─── Event Log (from database) ──────────────────────────────────────

@router.get(
    "/events/{session_id}",
    response_model=EventLogResponse,
    summary="Get WhatsApp events from database",
)
async def get_event_log(
    session_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    event_type: str = Query(default="", description="Filter by event type"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    wa_service: WhatsAppService = Depends(_get_whatsapp_service),
):
    """
    Get WhatsApp events from the database for a session.

    This provides persistent event history including connection attempts,
    QR scans, messages sent/received, and errors.
    """
    conn = wa_service.get_connection(session_id)

    # Verify ownership if connection exists
    if conn and conn.bot_id:
        from sqlalchemy import select
        from backend.models import Bot
        result = await db.execute(select(Bot).where(Bot.id == conn.bot_id))
        bot = result.scalar_one_or_none()
        if bot and str(bot.owner_id) != str(current_user.id):
            await require_role("admin")(current_user)

    events = await wa_service.get_events_from_db(
        session_id, limit=limit, event_type=event_type
    )

    return EventLogResponse(
        session_id=session_id,
        events=[
            EventLogEntry(
                id=e["id"],
                event_type=e["event_type"],
                message=e["message"],
                details=e["details"],
                phone_number=e["phone_number"],
                created_at=datetime.fromisoformat(e["created_at"]),
            )
            for e in events
        ],
        total=len(events),
    )
