"""WhatsApp Endpoints — API REST para gerenciamento de conexões WhatsApp."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.core.whatsapp_manager import WhatsAppManager
from backend.models.bot import Bot
from backend.models.user import User
from backend.models.whatsapp_session import WhatsAppSession
from backend.services.bot_service import BotService
from backend.services.whatsapp_service import WhatsAppService
from backend.config import settings

router = APIRouter()

# Instância global do WhatsApp Manager
whatsapp_manager = WhatsAppManager()


class SendMessageRequest(BaseModel):
    to: str = Field(..., description="Número de destino (com código do país)")
    message: str = Field(..., min_length=1, max_length=10000)


class CreateSessionRequest(BaseModel):
    bot_id: str = Field(..., description="ID do bot")


# ─── Sessões WhatsApp ─────────────────────────────────────

@router.get("/sessions")
async def list_whatsapp_sessions(
    bot_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista sessões WhatsApp de um bot."""
    bot = await BotService.get_bot(db, bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    sessions = await WhatsAppService.list_sessions(db, bot_id)
    return {
        "sessions": [
            {
                "id": str(s.id),
                "bot_id": str(s.bot_id),
                "session_name": s.session_name,
                "status": s.status.value if hasattr(s.status, 'value') else str(s.status),
                "phone_number": s.phone_number,
                "phone_name": s.phone_name,
                "connected_at": s.connected_at.isoformat() if s.connected_at else None,
                "last_seen": s.last_seen.isoformat() if s.last_seen else None,
                "reconnect_attempts": s.reconnect_attempts,
            }
            for s in sessions
        ],
        "total": len(sessions),
    }


@router.post("/sessions")
async def create_whatsapp_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cria uma nova sessão WhatsApp."""
    bot = await BotService.get_bot(db, request.bot_id, str(current_user.id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    # Criar sessão no banco
    session = await WhatsAppService.create_session(db, request.bot_id)

    # Criar sessão no manager
    ws_session = await whatsapp_manager.create_session(request.bot_id)

    # Atualizar session_data com o ID do manager
    session.session_data = {"manager_session_id": ws_session.session_id}
    await db.commit()

    return {
        "id": str(session.id),
        "bot_id": request.bot_id,
        "status": "disconnected",
        "message": "Sessão criada. Use /connect para gerar QR Code.",
    }


@router.get("/sessions/{session_id}")
async def get_whatsapp_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém detalhes de uma sessão WhatsApp."""
    session = await WhatsAppService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    return {
        "id": str(session.id),
        "bot_id": str(session.bot_id),
        "session_name": session.session_name,
        "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
        "phone_number": session.phone_number,
        "phone_name": session.phone_name,
        "qr_code": session.qr_code if not session.qr_expires_at or session.qr_expires_at else None,
        "connected_at": session.connected_at.isoformat() if session.connected_at else None,
        "last_seen": session.last_seen.isoformat() if session.last_seen else None,
    }


@router.post("/sessions/{session_id}/connect")
async def connect_whatsapp(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Inicia conexão WhatsApp (gera QR Code)."""
    session = await WhatsAppService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    # Verificar se já está conectado
    status_val = session.status.value if hasattr(session.status, 'value') else str(session.status)
    if status_val == "connected":
        return {"message": "WhatsApp já está conectado", "status": "connected"}

    # Iniciar conexão
    try:
        # Buscar manager session ID
        manager_session_id = None
        if session.session_data and isinstance(session.session_data, dict):
            manager_session_id = session.session_data.get("manager_session_id")

        if manager_session_id:
            ws_session = await whatsapp_manager.get_session(manager_session_id)
        else:
            ws_session = await whatsapp_manager.create_session(str(session.bot_id))
            session.session_data = {"manager_session_id": ws_session.session_id}

        result = await whatsapp_manager.connect(ws_session.session_id)

        # Atualizar banco
        await WhatsAppService.update_status(
            db, session_id,
            __import__('backend.models.whatsapp_session', fromlist=['SessionStatus']).SessionStatus.QR_REQUIRED,
        )

        if result.get("qr_code"):
            from datetime import datetime, timedelta
            await WhatsAppService.update_qr(
                db, session_id,
                result["qr_code"],
                expires_in_seconds=60,
            )

        return {
            "status": "qr_required",
            "qr_code": result.get("qr_code"),
            "expires_at": result.get("expires_at"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar: {str(e)}")


@router.get("/sessions/{session_id}/qr")
async def get_qr_code(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém QR Code de uma sessão."""
    session = await WhatsAppService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    # Verificar se QR expirou
    from datetime import datetime
    if session.qr_expires_at and session.qr_expires_at < datetime.utcnow():
        # Regenerar
        try:
            manager_session_id = None
            if session.session_data and isinstance(session.session_data, dict):
                manager_session_id = session.session_data.get("manager_session_id")

            if manager_session_id:
                ws_session = await whatsapp_manager.get_session(manager_session_id)
                if ws_session:
                    result = await whatsapp_manager.connect(ws_session.session_id)
                    return {
                        "qr_code": result.get("qr_code"),
                        "expires_at": result.get("expires_at"),
                    }
        except Exception:
            pass

        raise HTTPException(status_code=400, detail="QR Code expirou. Gere um novo.")

    return {
        "qr_code": session.qr_code,
        "expires_at": session.qr_expires_at.isoformat() if session.qr_expires_at else None,
    }


@router.post("/sessions/{session_id}/disconnect")
async def disconnect_whatsapp(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Desconecta uma sessão WhatsApp."""
    session = await WhatsAppService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    # Desconectar no manager
    try:
        manager_session_id = None
        if session.session_data and isinstance(session.session_data, dict):
            manager_session_id = session.session_data.get("manager_session_id")

        if manager_session_id:
            ws_session = await whatsapp_manager.get_session(manager_session_id)
            if ws_session:
                await whatsapp_manager.disconnect(ws_session.session_id)
    except Exception:
        pass

    # Atualizar banco
    await WhatsAppService.disconnect_session(db, session_id)

    return {"message": "WhatsApp desconectado", "status": "disconnected"}


@router.delete("/sessions/{session_id}")
async def delete_whatsapp_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deleta uma sessão WhatsApp."""
    session = await WhatsAppService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    # Desconectar primeiro
    try:
        manager_session_id = None
        if session.session_data and isinstance(session.session_data, dict):
            manager_session_id = session.session_data.get("manager_session_id")

        if manager_session_id:
            await whatsapp_manager.delete_session(manager_session_id)
    except Exception:
        pass

    # Deletar do banco
    await WhatsAppService.delete_session(db, session_id)

    return {"message": "Sessão deletada"}


# ─── Envio de Mensagens ──────────────────────────────────

@router.post("/send")
async def send_whatsapp_message(
    session_id: str = Query(...),
    request: SendMessageRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Envia mensagem pelo WhatsApp."""
    session = await WhatsAppService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    status_val = session.status.value if hasattr(session.status, 'value') else str(session.status)
    if status_val != "connected":
        raise HTTPException(status_code=400, detail="WhatsApp não está conectado")

    try:
        manager_session_id = None
        if session.session_data and isinstance(session.session_data, dict):
            manager_session_id = session.session_data.get("manager_session_id")

        if manager_session_id:
            ws_session = await whatsapp_manager.get_session(manager_session_id)
            if ws_session:
                result = await whatsapp_manager.send_message(
                    ws_session.session_id,
                    request.to,
                    request.message,
                )
                return result

        raise HTTPException(status_code=500, detail="Erro ao enviar mensagem")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar: {str(e)}")


# ─── Webhook (chamado pelo connector) ────────────────────

@router.post("/webhook")
async def whatsapp_webhook(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Recebe webhooks do WhatsApp connector."""
    result = await whatsapp_manager.handle_webhook(payload)

    # Processar eventos
    event_type = payload.get("event")

    if event_type == "connected":
        session_id = payload.get("session_id")
        data = payload.get("data", {})
        # Atualizar todas as sessões que usam este manager_session_id
        sessions_result = await db.execute(
            select(WhatsAppSession).where(
                WhatsAppSession.session_data.contains({"manager_session_id": session_id})
            )
        )
        for s in sessions_result.scalars().all():
            await WhatsAppService.update_status(
                db, str(s.id),
                __import__('backend.models.whatsapp_session', fromlist=['SessionStatus']).SessionStatus.CONNECTED,
                phone_number=data.get("phone_number"),
                phone_name=data.get("phone_name"),
            )

    elif event_type == "disconnected":
        session_id = payload.get("session_id")
        sessions_result = await db.execute(
            select(WhatsAppSession).where(
                WhatsAppSession.session_data.contains({"manager_session_id": session_id})
            )
        )
        for s in sessions_result.scalars().all():
            await WhatsAppService.disconnect_session(db, str(s.id))

    return result


# ─── Status ───────────────────────────────────────────────

@router.get("/sessions/{session_id}/status")
async def get_whatsapp_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém status de uma sessão WhatsApp."""
    session = await WhatsAppService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    status_val = session.status.value if hasattr(session.status, 'value') else str(session.status)

    # Verificar se processo ainda está ativo
    manager_session_id = None
    if session.session_data and isinstance(session.session_data, dict):
        manager_session_id = session.session_data.get("manager_session_id")

    if manager_session_id:
        try:
            ws_check = await whatsapp_manager.check_connection(manager_session_id)
            if ws_check.get("status") == "connected":
                status_val = "connected"
        except Exception:
            pass

    return {
        "session_id": session_id,
        "status": status_val,
        "phone_number": session.phone_number,
        "phone_name": session.phone_name,
        "connected_at": session.connected_at.isoformat() if session.connected_at else None,
        "last_seen": session.last_seen.isoformat() if session.last_seen else None,
    }
