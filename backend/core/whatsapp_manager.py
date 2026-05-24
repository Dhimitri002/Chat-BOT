"""WhatsApp Manager - Gerenciador de conexões WhatsApp via Baileys (Node.js subprocess)."""
import asyncio
import base64
import json
import os
import subprocess
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Optional
from uuid import uuid4


class WhatsAppSession:
    """Representa uma sessão WhatsApp ativa."""

    def __init__(self, session_id: str, bot_id: str):
        self.session_id = session_id
        self.bot_id = bot_id
        self.status = "disconnected"  # disconnected, connecting, connected, qr_required
        self.qr_code: Optional[str] = None
        self.qr_expires_at: Optional[datetime] = None
        self.phone_number: Optional[str] = None
        self.phone_name: Optional[str] = None
        self.connected_at: Optional[datetime] = None
        self.last_seen: Optional[datetime] = None
        self.process: Optional[subprocess.Popen] = None
        self.message_handlers: list[Callable] = []
        self.reconnect_attempts: int = 0
        self.max_reconnect_attempts: int = 3


class WhatsAppManager:
    """
    Gerenciador de conexões WhatsApp.

    Gerencia múltiplas sessões WhatsApp via subprocessos Node.js (Baileys).
    Cada bot pode ter uma sessão WhatsApp independente.
    """

    def __init__(self, connector_path: Optional[str] = None):
        self._sessions: dict[str, WhatsAppSession] = {}
        self.connector_path = connector_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "whatsapp-connector"
        )

    def _get_session_dir(self, session_id: str) -> str:
        """Retorna diretório de sessão."""
        session_dir = os.path.join(self.connector_path, "sessions", session_id)
        os.makedirs(session_dir, exist_ok=True)
        return session_dir

    async def create_session(self, bot_id: str) -> WhatsAppSession:
        """Cria uma nova sessão WhatsApp."""
        session_id = str(uuid4())
        session = WhatsAppSession(session_id=session_id, bot_id=bot_id)
        self._sessions[session_id] = session
        return session

    async def get_session(self, session_id: str) -> Optional[WhatsAppSession]:
        """Retorna sessão pelo ID."""
        return self._sessions.get(session_id)

    async def list_sessions(self, bot_id: Optional[str] = None) -> list[WhatsAppSession]:
        """Lista sessões, opcionalmente filtradas por bot_id."""
        sessions = list(self._sessions.values())
        if bot_id:
            sessions = [s for s in sessions if s.bot_id == bot_id]
        return sessions

    async def connect(self, session_id: str) -> dict:
        """
        Inicia conexão WhatsApp (gera QR Code).

        Returns:
            dict com qr_code (base64), expires_at
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Sessão não encontrada")

        session.status = "connecting"
        session.reconnect_attempts = 0

        try:
            # Iniciar processo Node.js do conector
            connector_script = os.path.join(self.connector_path, "src", "index.js")

            if not os.path.exists(connector_script):
                # Se não existe o conector Node.js, gerar QR simulado para desenvolvimento
                return await self._generate_dev_qr(session)

            session.process = subprocess.Popen(
                [
                    "node", connector_script,
                    "--session-id", session_id,
                    "--session-dir", self._get_session_dir(session_id),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
            )

            # Aguardar QR Code do processo
            qr_data = await self._wait_for_qr(session)

            session.status = "qr_required"
            session.qr_code = qr_data["qr_code"]
            session.qr_expires_at = datetime.utcnow() + timedelta(seconds=60)

            return {
                "qr_code": qr_data["qr_code"],
                "expires_at": session.qr_expires_at.isoformat(),
            }

        except Exception as e:
            session.status = "disconnected"
            raise ConnectionError(f"Erro ao iniciar conexão WhatsApp: {str(e)}")

    async def _generate_dev_qr(self, session: WhatsAppSession) -> dict:
        """Gera QR Code de desenvolvimento (quando conector Node.js não existe)."""
        import qrcode
        from io import BytesIO

        # QR Code de desenvolvimento
        dev_data = json.dumps({
            "session_id": session.session_id,
            "bot_id": session.bot_id,
            "timestamp": time.time(),
        })

        qr = qrcode.make(dev_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        session.status = "qr_required"
        session.qr_code = qr_base64
        session.qr_expires_at = datetime.utcnow() + timedelta(minutes=5)

        return {
            "qr_code": qr_base64,
            "expires_at": session.qr_expires_at.isoformat(),
        }

    async def _wait_for_qr(self, session: WhatsAppSession, timeout: int = 30) -> dict:
        """Aguarda QR Code do processo Node.js."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if session.process and session.process.stdout:
                try:
                    line = session.process.stdout.readline()
                    if line:
                        data = json.loads(line.decode().strip())
                        if data.get("type") == "qr":
                            return {"qr_code": data["qr"]}
                except (json.JSONDecodeError, Exception):
                    pass

            await asyncio.sleep(0.5)

        raise TimeoutError("Timeout aguardando QR Code")

    async def check_connection(self, session_id: str) -> dict:
        """Verifica status da conexão."""
        session = self._sessions.get(session_id)
        if not session:
            return {"status": "not_found"}

        # Verificar se processo ainda está rodando
        if session.process and session.process.poll() is not None:
            # Processo morreu
            session.status = "disconnected"
            session.process = None

            # Tentar reconectar
            if session.reconnect_attempts < session.max_reconnect_attempts:
                session.reconnect_attempts += 1
                try:
                    await self.connect(session_id)
                    session.status = "connecting"
                except Exception:
                    pass

        return {
            "status": session.status,
            "phone_number": session.phone_number,
            "phone_name": session.phone_name,
            "connected_at": session.connected_at.isoformat() if session.connected_at else None,
            "last_seen": session.last_seen.isoformat() if session.last_seen else None,
            "reconnect_attempts": session.reconnect_attempts,
        }

    async def disconnect(self, session_id: str) -> bool:
        """Desconecta uma sessão WhatsApp."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        # Parar processo Node.js
        if session.process:
            try:
                session.process.terminate()
                session.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                session.process.kill()
            except Exception:
                pass
            session.process = None

        session.status = "disconnected"
        session.qr_code = None
        session.qr_expires_at = None
        return True

    async def send_message(
        self, session_id: str, to: str, message: str, message_type: str = "text"
    ) -> dict:
        """
        Envia mensagem pelo WhatsApp.

        Args:
            session_id: ID da sessão
            to: Número de destino (com código do país, ex: 5511999999999)
            message: Texto da mensagem
            message_type: Tipo (text, image, document)

        Returns:
            dict com message_id, status
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Sessão não encontrada")

        if session.status != "connected":
            raise ConnectionError("WhatsApp não está conectado")

        message_id = str(uuid4())

        # Enviar via processo Node.js
        if session.process and session.process.stdin:
            try:
                payload = json.dumps({
                    "type": "send_message",
                    "to": to,
                    "message": message,
                    "message_type": message_type,
                    "message_id": message_id,
                })
                session.process.stdin.write(payload.encode() + b"\n")
                session.process.stdin.flush()
            except Exception as e:
                raise ConnectionError(f"Erro ao enviar mensagem: {str(e)}")

        return {
            "message_id": message_id,
            "status": "sent",
            "to": to,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def handle_webhook(self, payload: dict) -> dict:
        """
        Processa webhook recebido do WhatsApp.

        Args:
            payload: Dados do webhook

        Returns:
            dict com resultado do processamento
        """
        event_type = payload.get("event")
        session_id = payload.get("session_id")

        if event_type == "message":
            # Mensagem recebida
            message_data = payload.get("data", {})

            # Notificar handlers
            session = self._sessions.get(session_id)
            if session:
                for handler in session.message_handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(message_data)
                        else:
                            handler(message_data)
                    except Exception:
                        pass

            return {"status": "processed", "type": "message"}

        elif event_type == "connected":
            # Conexão estabelecida
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.status = "connected"
                session.connected_at = datetime.utcnow()
                session.phone_number = payload.get("data", {}).get("phone_number")
                session.phone_name = payload.get("data", {}).get("phone_name")
                session.reconnect_attempts = 0

            return {"status": "processed", "type": "connected"}

        elif event_type == "disconnected":
            # Conexão perdida
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.status = "disconnected"

            return {"status": "processed", "type": "disconnected"}

        elif event_type == "qr":
            # QR Code atualizado
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.qr_code = payload.get("data", {}).get("qr")
                session.qr_expires_at = datetime.utcnow() + timedelta(seconds=60)

            return {"status": "processed", "type": "qr"}

        return {"status": "unknown_event", "type": event_type}

    def register_message_handler(self, session_id: str, handler: Callable):
        """Registra handler para mensagens recebidas."""
        session = self._sessions.get(session_id)
        if session:
            session.message_handlers.append(handler)

    async def delete_session(self, session_id: str) -> bool:
        """Deleta uma sessão completamente."""
        session = self._sessions.pop(session_id, None)
        if not session:
            return False

        await self.disconnect(session_id)

        # Limpar arquivos de sessão
        session_dir = self._get_session_dir(session_id)
        if os.path.exists(session_dir):
            import shutil
            shutil.rmtree(session_dir, ignore_errors=True)

        return True

    async def get_qr_code(self, session_id: str) -> Optional[str]:
        """Retorna QR Code atual da sessão."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        # Verificar se QR expirou
        if session.qr_expires_at and session.qr_expires_at < datetime.utcnow():
            # Regenerar QR
            try:
                result = await self.connect(session_id)
                return result.get("qr_code")
            except Exception:
                return None

        return session.qr_code
