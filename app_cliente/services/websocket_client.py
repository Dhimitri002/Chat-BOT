"""WebSocket Client — Cliente WebSocket para comunicação em tempo real com o backend."""
import json
import threading
import time
from typing import Any, Callable, Optional


class WebSocketClient:
    """
    Cliente WebSocket para atualizações em tempo real.

    Suporta:
    - Conexão automática com retry
    - Reconexão em caso de perda
    - Registro de handlers por evento
    - Heartbeat/ping para manter conexão viva
    - Fallback para HTTP polling quando WebSocket não está disponível
    """

    def __init__(
        self,
        url: str = "ws://localhost:8000/ws",
        auto_reconnect: bool = True,
        reconnect_delay: float = 3.0,
        max_reconnect_delay: float = 30.0,
        heartbeat_interval: float = 30.0,
    ):
        self.url = url
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay
        self.heartbeat_interval = heartbeat_interval

        self._ws = None
        self._connected = False
        self._running = False
        self._handlers: dict[str, list[Callable]] = {}
        self._thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._current_delay = reconnect_delay
        self._token: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        """Verifica se está conectado."""
        return self._connected

    def set_token(self, token: str):
        """Define token de autenticação."""
        self._token = token

    def connect(self):
        """Inicia conexão WebSocket em thread separada."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def disconnect(self):
        """Desconecta o WebSocket."""
        self._running = False
        self._connected = False

        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None

    def _run(self):
        """Loop principal de conexão."""
        while self._running:
            try:
                self._connect_and_listen()
            except Exception as e:
                print(f"[WebSocket] Erro: {e}")

            if not self.auto_reconnect or not self._running:
                break

            time.sleep(self._current_delay)
            self._current_delay = min(
                self._current_delay * 2,
                self.max_reconnect_delay,
            )

    def _connect_and_listen(self):
        """Conecta e escuta mensagens."""
        try:
            import websocket

            headers = {}
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"

            self._ws = websocket.WebSocketApp(
                self.url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                header=headers,
            )

            self._ws.run_forever(ping_interval=self.heartbeat_interval)

        except ImportError:
            print("[WebSocket] websocket-client não instalado. Usando polling fallback.")
            self._polling_fallback()

    def _polling_fallback(self):
        """Fallback usando HTTP polling quando WebSocket não está disponível."""
        import urllib.request

        while self._running:
            try:
                url = self.url.replace("ws://", "http://").replace("wss://", "https://")
                url += "/poll"

                headers = {"Content-Type": "application/json"}
                if self._token:
                    headers["Authorization"] = f"Bearer {self._token}"

                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = json.loads(response.read().decode())
                    if data:
                        self._dispatch_events(data)

            except Exception as e:
                print(f"[WebSocket] Polling error: {e}")

            time.sleep(5)

    def _on_open(self, ws):
        """Callback quando conexão é estabelecida."""
        self._connected = True
        self._current_delay = self.reconnect_delay
        self._dispatch("connected", {})

        if self.heartbeat_interval > 0:
            self._heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop, daemon=True
            )
            self._heartbeat_thread.start()

    def _on_message(self, ws, message: str):
        """Callback quando mensagem é recebida."""
        try:
            data = json.loads(message)
            event_type = data.get("type", "message")
            event_data = data.get("data", data)
            self._dispatch(event_type, event_data)
        except json.JSONDecodeError:
            self._dispatch("message", {"raw": message})

    def _on_error(self, ws, error):
        """Callback quando ocorre erro."""
        self._dispatch("error", {"error": str(error)})

    def _on_close(self, ws, close_status_code, close_msg):
        """Callback quando conexão é fechada."""
        self._connected = False
        self._dispatch("disconnected", {
            "code": close_status_code,
            "message": close_msg,
        })

    def _heartbeat_loop(self):
        """Loop de heartbeat para manter conexão viva."""
        while self._running and self._connected:
            try:
                if self._ws:
                    self._ws.send(json.dumps({"type": "ping"}))
            except Exception:
                pass
            time.sleep(self.heartbeat_interval)

    def send(self, data: dict):
        """Envia mensagem pelo WebSocket."""
        if self._ws and self._connected:
            try:
                self._ws.send(json.dumps(data))
            except Exception as e:
                print(f"[WebSocket] Erro ao enviar: {e}")

    def on(self, event_type: str, handler: Callable):
        """Registra handler para um tipo de evento."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: Optional[Callable] = None):
        """Remove handler de um tipo de evento."""
        if event_type in self._handlers:
            if handler:
                self._handlers[event_type] = [
                    h for h in self._handlers[event_type] if h != handler
                ]
            else:
                self._handlers[event_type] = []

    def _dispatch(self, event_type: str, data: Any):
        """Dispara handlers para um evento."""
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"[WebSocket] Handler error: {e}")

        # Wildcard handlers
        for handler in self._handlers.get("*", []):
            try:
                handler(event_type, data)
            except Exception as e:
                print(f"[WebSocket] Wildcard handler error: {e}")

    def _dispatch_events(self, events: list):
        """Dispara eventos recebidos via polling."""
        if isinstance(events, list):
            for event in events:
                event_type = event.get("type", "message")
                event_data = event.get("data", event)
                self._dispatch(event_type, event_data)


# Instância global
ws_client = WebSocketClient(
    url="ws://localhost:8000/ws",
    auto_reconnect=True,
)
