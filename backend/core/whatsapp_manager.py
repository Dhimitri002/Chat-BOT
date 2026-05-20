"""
WhatsApp Connection Manager
Gerencia múltiplas sessões de WhatsApp, uma por bot.
Usa o whatsapp-bot (Node.js) como bridge via subprocess + WebSocket.
"""
import asyncio
import json
import os
import signal
import subprocess
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import aiohttp
from loguru import logger


class WhatsAppState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    PAIRING = "pairing"  # Aguardando scan do QR
    CONNECTED = "connected"
    ERROR = "error"
    LOGGED_OUT = "logged_out"


class WhatsAppSession:
    """Representa uma sessão de WhatsApp para um bot específico."""

    def __init__(self, bot_id: str, user_id: str, session_dir: str = "whatsapp-bot/sessions"):
        self.bot_id = bot_id
        self.user_id = user_id
        self.session_id = str(uuid.uuid4())[:8]
        self.state = WhatsAppState.DISCONNECTED
        self.phone_number: Optional[str] = None
        self.bot_name: Optional[str] = None
        self.qr_code: Optional[str] = None  # base64 image
        self.qr_expiry: Optional[float] = None
        self.connected_at: Optional[datetime] = None
        self.disconnected_at: Optional[datetime] = None
        self.battery_level: Optional[int] = None
        self.platform: Optional[str] = None
        self.last_error: Optional[str] = None
        self.reconnect_count: int = 0
        self.max_reconnect: int = 10
        self.reconnect_delay: float = 2.0
        self.process: Optional[subprocess.Popen] = None
        self._event_handlers: dict[str, list[Callable]] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._message_processor_task: Optional[asyncio.Task] = None
        self.session_dir = Path(session_dir) / bot_id
        self._ws_url: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "bot_id": self.bot_id,
            "session_id": self.session_id,
            "state": self.state.value,
            "phone_number": self.phone_number,
            "bot_name": self.bot_name,
            "qr_code": self.qr_code,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "disconnected_at": self.disconnected_at.isoformat() if self.disconnected_at else None,
            "battery_level": self.battery_level,
            "platform": self.platform,
            "last_error": self.last_error,
            "reconnect_count": self.reconnect_count,
        }

    def on(self, event: str, handler: Callable):
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    async def emit(self, event: str, data: Any = None):
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Event handler error for {event}: {e}")


class WhatsAppManager:
    """
    Gerenciador central de sessões WhatsApp.
    Mantém um dicionário de sessões ativas, uma por bot.
    """

    def __init__(self, node_script: str = "whatsapp-bot/index.js", ws_port: int = 3010):
        self.sessions: dict[str, WhatsAppSession] = {}
        self.node_script = Path(node_script)
        self.ws_port = ws_port
        self._global_handlers: dict[str, list[Callable]] = {}
        self._node_process: Optional[subprocess.Popen] = None
        self._ws_server_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Inicia o gerenciador WhatsApp."""
        if self._running:
            return
        self._running = True
        logger.info("WhatsApp Manager iniciado")

        # Garantir que o diretório de sessões existe
        Path("whatsapp-bot/sessions").mkdir(parents=True, exist_ok=True)

        # Iniciar servidor WebSocket interno para comunicação com apps
        self._ws_server_task = asyncio.create_task(self._run_ws_server())

    async def stop(self):
        """Para todas as sessões e o gerenciador."""
        self._running = False

        # Desconectar todas as sessões
        for bot_id in list(self.sessions.keys()):
            await self.disconnect(bot_id)

        if self._ws_server_task:
            self._ws_server_task.cancel()

        if self._node_process:
            self._node_process.terminate()
            self._node_process.wait(timeout=5)

        logger.info("WhatsApp Manager parado")

    def get_or_create_session(self, bot_id: str, user_id: str) -> WhatsAppSession:
        if bot_id not in self.sessions:
            session = WhatsAppSession(bot_id, user_id)
            # Registrar handlers padrão
            session.on("qr", self._on_qr)
            session.on("connected", self._on_connected)
            session.on("disconnected", self._on_disconnected)
            session.on("message", self._on_message)
            session.on("error", self._on_error)
            self.sessions[bot_id] = session
        return self.sessions[bot_id]

    async def connect(self, bot_id: str, user_id: str) -> WhatsAppSession:
        """Inicia conexão WhatsApp para um bot."""
        session = self.get_or_create_session(bot_id, user_id)

        if session.state in (WhatsAppState.CONNECTED, WhatsAppState.CONNECTING, WhatsAppState.PAIRING):
            logger.warning(f"Bot {bot_id} já está {session.state.value}")
            return session

        session.state = WhatsAppState.CONNECTING
        session.last_error = None
        session.qr_code = None

        try:
            # Iniciar processo Node.js para este bot
            await self._start_node_session(session)
            await session.emit("state_change", session.to_dict())
        except Exception as e:
            session.state = WhatsAppState.ERROR
            session.last_error = str(e)
            logger.error(f"Erro ao conectar bot {bot_id}: {e}")
            await session.emit("error", {"bot_id": bot_id, "error": str(e)})

        return session

    async def disconnect(self, bot_id: str):
        """Desconecta um bot."""
        session = self.sessions.get(bot_id)
        if not session:
            return

        session._running = False

        # Cancelar tasks
        if session._health_check_task:
            session._health_check_task.cancel()
        if session._message_processor_task:
            session._message_processor_task.cancel()

        # Parar processo Node.js
        if session.process:
            try:
                session.process.terminate()
                session.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                session.process.kill()
            except Exception:
                pass

        session.state = WhatsAppState.DISCONNECTED
        session.disconnected_at = datetime.now(timezone.utc)
        session.qr_code = None
        await session.emit("state_change", session.to_dict())
        await session.emit("disconnected", session.to_dict())
        logger.info(f"Bot {bot_id} desconectado")

    async def restart(self, bot_id: str) -> WhatsAppSession:
        """Reinicia a conexão de um bot."""
        session = self.sessions.get(bot_id)
        user_id = session.user_id if session else "unknown"
        await self.disconnect(bot_id)
        await asyncio.sleep(1)
        return await self.connect(bot_id, user_id)

    async def logout(self, bot_id: str):
        """Faz logout e limpa dados da sessão."""
        session = self.sessions.get(bot_id)
        if not session:
            return

        await self.disconnect(bot_id)

        # Limpar diretório de sessão
        import shutil
        if session.session_dir.exists():
            shutil.rmtree(session.session_dir, ignore_errors=True)

        session.state = WhatsAppState.LOGGED_OUT
        session.phone_number = None
        session.bot_name = None
        session.reconnect_count = 0
        await session.emit("state_change", session.to_dict())
        logger.info(f"Bot {bot_id} logout completo")

    def get_status(self, bot_id: str) -> Optional[dict]:
        session = self.sessions.get(bot_id)
        return session.to_dict() if session else None

    def get_all_sessions(self) -> list[dict]:
        return [s.to_dict() for s in self.sessions.values()]

    async def send_message(self, bot_id: str, to: str, text: str) -> dict:
        """Envia mensagem de texto."""
        session = self.sessions.get(bot_id)
        if not session or session.state != WhatsAppState.CONNECTED:
            return {"success": False, "error": "Bot não está conectado"}

        message_id = str(uuid.uuid4())
        await session._message_queue.put({
            "type": "send_message",
            "message_id": message_id,
            "to": to,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(f"Mensagem enfileirada: {message_id} para {to}")
        return {"success": True, "message_id": message_id}

    async def send_media(self, bot_id: str, to: str, media_path: str, caption: str = "") -> dict:
        """Envia mídia (imagem, vídeo, documento)."""
        session = self.sessions.get(bot_id)
        if not session or session.state != WhatsAppState.CONNECTED:
            return {"success": False, "error": "Bot não está conectado"}

        message_id = str(uuid.uuid4())
        await session._message_queue.put({
            "type": "send_media",
            "message_id": message_id,
            "to": to,
            "media_path": media_path,
            "caption": caption,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {"success": True, "message_id": message_id}

    # --- Interno ---

    async def _start_node_session(self, session: WhatsAppSession):
        """Inicia o processo Node.js para uma sessão."""
        session.session_dir.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["BOT_ID"] = session.bot_id
        env["SESSION_ID"] = session.session_id
        env["SESSION_DIR"] = str(session.session_dir)
        env["WS_PORT"] = str(self.ws_port)
        env["BACKEND_URL"] = os.getenv("BACKEND_URL", "http://localhost:8000")

        cmd = ["node", str(self.node_script)]

        session.process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(self.node_script.parent),
        )

        session._running = True

        # Iniciar task de health check
        session._health_check_task = asyncio.create_task(self._health_check(session))

        # Iniciar task de processamento de mensagens
        session._message_processor_task = asyncio.create_task(self._process_messages(session))

        # Iniciar task de leitura do stdout do processo
        asyncio.create_task(self._read_stdout(session))

        logger.info(f"Processo Node.js iniciado para bot {session.bot_id} (PID: {session.process.pid})")

    async def _read_stdout(self, session: WhatsAppSession):
        """Lê stdout do processo Node.js e processa eventos."""
        if not session.process or not session.process.stdout:
            return

        try:
            while session._running and session.process.poll() is None:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, session.process.stdout.readline
                )
                if not line:
                    break

                line_str = line.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue

                try:
                    data = json.loads(line_str)
                    await self._handle_node_event(session, data)
                except json.JSONDecodeError:
                    # Log normal do Node.js
                    logger.debug(f"[Node/{session.bot_id}] {line_str}")
        except Exception as e:
            logger.error(f"Erro lendo stdout do bot {session.bot_id}: {e}")

    async def _handle_node_event(self, session: WhatsAppSession, data: dict):
        """Processa eventos recebidos do processo Node.js."""
        event_type = data.get("type")

        if event_type == "qr":
            session.state = WhatsAppState.PAIRING
            session.qr_code = data.get("qr")
            session.qr_expiry = time.time() + data.get("expires_in", 60)
            await session.emit("qr", {"bot_id": session.bot_id, "qr": session.qr_code})
            logger.info(f"QR Code gerado para bot {session.bot_id}")

        elif event_type == "connected":
            session.state = WhatsAppState.CONNECTED
            session.phone_number = data.get("phone")
            session.bot_name = data.get("name")
            session.connected_at = datetime.now(timezone.utc)
            session.reconnect_count = 0
            await session.emit("connected", session.to_dict())
            logger.info(f"Bot {session.bot_id} conectado como {session.phone_number}")

        elif event_type == "disconnected":
            session.state = WhatsAppState.DISCONNECTED
            session.disconnected_at = datetime.now(timezone.utc)
            reason = data.get("reason", "unknown")
            await session.emit("disconnected", {"bot_id": session.bot_id, "reason": reason})
            logger.info(f"Bot {session.bot_id} desconectado: {reason}")

            # Tentar reconexão automática
            if session._running and reason not in ("loggedOut", "intentional"):
                await self._auto_reconnect(session)

        elif event_type == "message":
            # Mensagem recebida do WhatsApp
            msg_data = data.get("message", {})
            await session.emit("message", msg_data)
            await self._route_incoming_message(session, msg_data)

        elif event_type == "message_sent":
            # Confirmação de envio
            await session.emit("message_sent", data)

        elif event_type == "battery":
            session.battery_level = data.get("level")
            session.platform = data.get("platform")

        elif event_type == "error":
            session.last_error = data.get("error")
            await session.emit("error", {"bot_id": session.bot_id, "error": session.last_error})
            logger.error(f"Erro no bot {session.bot_id}: {session.last_error}")

        # Emitir mudança de estado
        await session.emit("state_change", session.to_dict())

    async def _route_incoming_message(self, session: WhatsAppSession, msg_data: dict):
        """Roteia mensagem recebida para o chat engine."""
        try:
            from backend.services.chat_service import ChatService
            from backend.database import async_session

            async with async_session() as db:
                chat_service = ChatService(db)
                await chat_service.handle_incoming_message(
                    bot_id=session.bot_id,
                    sender=msg_data.get("from", ""),
                    text=msg_data.get("body", ""),
                    message_type=msg_data.get("type", "text"),
                    metadata=msg_data,
                )
        except Exception as e:
            logger.error(f"Erro ao rotear mensagem: {e}")

    async def _auto_reconnect(self, session: WhatsAppSession):
        """Tenta reconexão automática com backoff exponencial."""
        if session.reconnect_count >= session.max_reconnect:
            logger.warning(f"Bot {session.bot_id}: máximo de reconexões atingido")
            session.state = WhatsAppState.ERROR
            session.last_error = "Máximo de reconexões atingido"
            await session.emit("state_change", session.to_dict())
            return

        session.reconnect_count += 1
        delay = min(session.reconnect_delay * (2 ** (session.reconnect_count - 1)), 120)

        logger.info(f"Bot {session.bot_id}: reconectando em {delay}s (tentativa {session.reconnect_count})")
        await asyncio.sleep(delay)

        if session._running:
            session.state = WhatsAppState.CONNECTING
            await session.emit("state_change", session.to_dict())
            try:
                await self._start_node_session(session)
            except Exception as e:
                logger.error(f"Erro na reconexão do bot {session.bot_id}: {e}")

    async def _health_check(self, session: WhatsAppSession):
        """Verifica saúde da sessão periodicamente."""
        try:
            while session._running:
                await asyncio.sleep(30)

                # Verificar se o processo ainda está rodando
                if session.process and session.process.poll() is not None:
                    logger.warning(f"Processo Node.js do bot {session.bot_id} morreu")
                    if session.state == WhatsAppState.CONNECTED:
                        session.state = WhatsAppState.DISCONNECTED
                        await self._auto_reconnect(session)

                # Verificar QR code expirado
                if session.state == WhatsAppState.PAIRING and session.qr_expiry:
                    if time.time() > session.qr_expiry:
                        logger.info(f"QR Code expirado para bot {session.bot_id}")
                        # Solicitar novo QR
                        if session.process and session.process.stdin:
                            try:
                                session.process.stdin.write(b'{"action":"refresh_qr"}\n')
                                session.process.stdin.flush()
                            except Exception:
                                pass

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Erro no health check do bot {session.bot_id}: {e}")

    async def _process_messages(self, session: WhatsAppSession):
        """Processa fila de mensagens para enviar."""
        try:
            while session._running:
                try:
                    msg = await asyncio.wait_for(session._message_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                if session.process and session.process.stdin:
                    try:
                        data = json.dumps(msg) + "\n"
                        session.process.stdin.write(data.encode())
                        session.process.stdin.flush()
                    except Exception as e:
                        logger.error(f"Erro ao enviar mensagem para Node.js: {e}")
        except asyncio.CancelledError:
            pass

    async def _run_ws_server(self):
        """Servidor WebSocket interno para comunicação com apps."""
        # Este é um placeholder - na produção usariamos websockets library
        # Por enquanto, a comunicação é via eventos internos
        try:
            while self._running:
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    # --- Handlers padrão ---

    async def _on_qr(self, data):
        await self._emit_global("qr", data)

    async def _on_connected(self, data):
        await self._emit_global("connected", data)

    async def _on_disconnected(self, data):
        await self._emit_global("disconnected", data)

    async def _on_message(self, data):
        await self._emit_global("message", data)

    async def _on_error(self, data):
        await self._emit_global("error", data)

    def on_global(self, event: str, handler: Callable):
        if event not in self._global_handlers:
            self._global_handlers[event] = []
        self._global_handlers[event].append(handler)

    async def _emit_global(self, event: str, data: Any = None):
        handlers = self._global_handlers.get(event, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Global handler error for {event}: {e}")


# Singleton
whatsapp_manager = WhatsAppManager()
