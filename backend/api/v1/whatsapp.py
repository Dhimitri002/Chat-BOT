"""WhatsApp Endpoints - API REST para gerenciamento de conexões WhatsApp."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.core.whatsapp_manager import WhatsAppState, whatsapp_manager

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


# --- Schemas ---

class SendMessageRequest(BaseModel):
    to: str = Field(..., description="Número de destino (com código do país)")
    text: str = Field(..., min_length=1, max_length=10000)


class SendMediaRequest(BaseModel):
    to: str = Field(..., description="Número de destino")
    media_data: str = Field(..., description="Dados da mídia em base64")
    media_mimetype: str = Field(default="image/jpeg")
    caption: str = Field(default="")


class WhatsAppStatusResponse(BaseModel):
    bot_id: str
    state: str
    phone_number: Optional[str] = None
    bot_name: Optional[str] = None
    qr_code: Optional[str] = None
    connected_at: Optional[str] = None
    battery_level: Optional[int] = None
    platform: Optional[str] = None
    last_error: Optional[str] = None
    reconnect_count: int = 0


# --- Endpoints ---

@router.get("/status/{bot_id}", response_model=WhatsAppStatusResponse)
async def get_whatsapp_status(
    bot_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém o status da conexão WhatsApp de um bot."""
    status = whatsapp_manager.get_status(bot_id)
    if not status:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return status


@router.post("/connect/{bot_id}")
async def connect_whatsapp(
    bot_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Inicia conexão WhatsApp para um bot. Retorna QR code se necessário."""
    session = await whatsapp_manager.connect(bot_id, current_user.id)
    return {
        "success": True,
        "state": session.state.value,
        "qr_code": session.qr_code,
        "message": "Conexão iniciada. Escaneie o QR code com seu WhatsApp."
        if session.state == WhatsAppState.PAIRING
        else "Conectando...",
    }


@router.post("/disconnect/{bot_id}")
async def disconnect_whatsapp(
    bot_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Desconecta a sessão WhatsApp de um bot."""
    await whatsapp_manager.disconnect(bot_id)
    return {"success": True, "message": "Desconectado com sucesso."}


@router.post("/restart/{bot_id}")
async def restart_whatsapp(
    bot_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reinicia a conexão WhatsApp de um bot."""
    session = await whatsapp_manager.restart(bot_id)
    return {
        "success": True,
        "state": session.state.value,
        "qr_code": session.qr_code,
        "message": "Reiniciado. Escaneie o QR code."
        if session.state == WhatsAppState.PAIRING
        else "Reconectando...",
    }


@router.get("/qr/{bot_id}")
async def get_qr_code(
    bot_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém o QR code atual para um bot."""
    session = whatsapp_manager.sessions.get(bot_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    if session.state == WhatsAppState.CONNECTED:
        return {"connected": True, "phone": session.phone_number}

    if not session.qr_code:
        raise HTTPException(status_code=400, detail="QR code não disponível. Inicie a conexão primeiro.")

    return {
        "connected": False,
        "qr_code": session.qr_code,
        "expires_in": max(0, int(session.qr_expiry - __import__("time").time())) if session.qr_expiry else 60,
    }


@router.post("/send/{bot_id}")
async def send_whatsapp_message(
    bot_id: str,
    request: SendMessageRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Envia mensagem de texto via WhatsApp."""
    result = await whatsapp_manager.send_message(bot_id, request.to, request.text)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/send-media/{bot_id}")
async def send_whatsapp_media(
    bot_id: str,
    request: SendMediaRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Envia mídia via WhatsApp."""
    result = await whatsapp_manager.send_media(
        bot_id, request.to, request.media_data, request.caption
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/sessions")
async def list_whatsapp_sessions(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista todas as sessões WhatsApp do usuário."""
    all_sessions = whatsapp_manager.get_all_sessions()
    # Filtrar apenas sessões do usuário atual
    user_sessions = [s for s in all_sessions if s.get("user_id") == current_user.id]
    return {"sessions": user_sessions, "total": len(user_sessions)}


@router.post("/logout/{bot_id}")
async def logout_whatsapp(
    bot_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Faz logout e limpa dados da sessão WhatsApp."""
    await whatsapp_manager.logout(bot_id)
    return {"success": True, "message": "Logout realizado. Dados da sessão removidos."}


# --- WebSocket ---

@router.websocket("/ws/{bot_id}")
async def whatsapp_websocket(websocket: WebSocket, bot_id: str):
    """WebSocket para atualizações em tempo real do status WhatsApp."""
    await websocket.accept()

    session = whatsapp_manager.sessions.get(bot_id)
    if not session:
        await websocket.close(code=4004, reason="Sessão não encontrada")
        return

    # Enviar estado atual
    await websocket.send_json({"type": "status", "data": session.to_dict()})

    # Registrar handler para enviar atualizações
    async def send_update(data):
        try:
            await websocket.send_json({"type": "update", "data": data})
        except Exception:
            pass

    session.on("state_change", send_update)
    session.on("qr", send_update)
    session.on("connected", send_update)
    session.on("disconnected", send_update)
    session.on("message", send_update)

    try:
        while True:
            # Manter conexão viva e processar comandos do cliente
            data = await websocket.receive_text()
            try:
                cmd = __import__("json").loads(data)
                action = cmd.get("action")

                if action == "ping":
                    await websocket.send_json({"type": "pong"})
                elif action == "get_status":
                    await websocket.send_json({"type": "status", "data": session.to_dict()})
            except Exception:
                pass
    except WebSocketDisconnect:
        pass
