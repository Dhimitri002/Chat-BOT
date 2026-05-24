"""API Client — Cliente HTTP para comunicação com o backend Flora."""
import json
import threading
import time
from typing import Any, Callable, Optional
from urllib.parse import urljoin

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class APIError(Exception):
    """Erro de API."""

    def __init__(self, message: str, status_code: int = 0, response: Any = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class APIClient:
    """
    Cliente HTTP para a API da Flora Platform.

    Suporta:
    - Requests com retry automático
    - Autenticação JWT (Bearer token)
    - Timeout configurável
    - Tratamento de erro padronizado
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._session = None

        if HAS_REQUESTS:
            self._session = requests.Session()
            self._session.headers.update({
                "Content-Type": "application/json",
                "Accept": "application/json",
            })

    @property
    def is_authenticated(self) -> bool:
        """Verifica se há token de autenticação."""
        return self._token is not None

    def set_token(self, token: str, refresh_token: Optional[str] = None):
        """Define o token de autenticação."""
        self._token = token
        self._refresh_token = refresh_token
        if self._session:
            self._session.headers["Authorization"] = f"Bearer {token}"

    def clear_token(self):
        """Remove o token de autenticação."""
        self._token = None
        self._refresh_token = None
        if self._session and "Authorization" in self._session.headers:
            del self._session.headers["Authorization"]

    def _get_url(self, endpoint: str) -> str:
        """Monta URL completa."""
        if endpoint.startswith("http"):
            return endpoint
        return urljoin(f"{self.base_url}/", endpoint.lstrip("/"))

    def _get_headers(self, extra: Optional[dict] = None) -> dict:
        """Monta headers da request."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if extra:
            headers.update(extra)
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        retry_count: int = 0,
    ) -> dict:
        """
        Faz request HTTP com retry automático.

        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API
            data: Dados do body (JSON)
            params: Query parameters
            headers: Headers extras
            retry_count: Contador de retry (interno)

        Returns:
            dict com resposta da API

        Raises:
            APIError: Em caso de erro
        """
        url = self._get_url(endpoint)
        merged_headers = self._get_headers(headers)

        last_error = None

        for attempt in range(retry_count + 1):
            try:
                if HAS_REQUESTS and self._session:
                    response = self._session.request(
                        method=method.upper(),
                        url=url,
                        json=data,
                        params=params,
                        headers=merged_headers,
                        timeout=self.timeout,
                    )

                    # Verificar status
                    if response.status_code == 401:
                        # Tentar refresh token
                        if self._refresh_token and attempt == 0:
                            try:
                                self._do_refresh_token()
                                merged_headers["Authorization"] = f"Bearer {self._token}"
                                continue
                            except APIError:
                                pass

                        raise APIError(
                            "Não autorizado. Faça login novamente.",
                            status_code=401,
                        )

                    if response.status_code == 429:
                        # Rate limit — esperar e retry
                        retry_after = int(response.headers.get("Retry-After", 5))
                        time.sleep(retry_after)
                        continue

                    if response.status_code >= 400:
                        error_data = {}
                        try:
                            error_data = response.json()
                        except Exception:
                            pass

                        error_msg = error_data.get("detail", f"Erro {response.status_code}")
                        raise APIError(
                            error_msg,
                            status_code=response.status_code,
                            response=error_data,
                        )

                    # Sucesso
                    try:
                        return response.json()
                    except Exception:
                        return {"success": True}

                else:
                    # Fallback sem requests (usando urllib)
                    return self._request_urllib(method, url, data, params, merged_headers)

            except APIError:
                raise
            except Exception as e:
                last_error = e
                if attempt < retry_count:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue

        raise APIError(
            f"Erro de conexão após {retry_count + 1} tentativas: {str(last_error)}",
            status_code=0,
        )

    def _request_urllib(
        self, method: str, url: str, data: Optional[dict],
        params: Optional[dict], headers: dict
    ) -> dict:
        """Fallback request usando urllib (quando requests não está disponível)."""
        import urllib.request
        import urllib.error
        import urllib.parse

        if params:
            url += "?" + urllib.parse.urlencode(params)

        body = None
        if data:
            body = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=body,
            headers=headers,
            method=method.upper(),
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_data = response.read().decode("utf-8")
                return json.loads(response_data) if response_data else {"success": True}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            try:
                error_data = json.loads(error_body)
                error_msg = error_data.get("detail", str(e))
            except Exception:
                error_msg = str(e)
            raise APIError(error_msg, status_code=e.code)

    def _do_refresh_token(self):
        """Tenta renovar o access token usando refresh token."""
        if not self._refresh_token:
            raise APIError("Sem refresh token")

        response = self._request(
            "POST",
            "/api/v1/auth/refresh",
            data={"refresh_token": self._refresh_token},
            retry_count=0,
        )

        self._token = response.get("access_token")
        if self._session:
            self._session.headers["Authorization"] = f"Bearer {self._token}"

    # ── Métodos HTTP públicos ──────────────────────────────

    def get(self, endpoint: str, params: Optional[dict] = None, **kwargs) -> dict:
        """GET request."""
        return self._request("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint: str, data: Optional[dict] = None, **kwargs) -> dict:
        """POST request."""
        return self._request("POST", endpoint, data=data, **kwargs)

    def put(self, endpoint: str, data: Optional[dict] = None, **kwargs) -> dict:
        """PUT request."""
        return self._request("PUT", endpoint, data=data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> dict:
        """DELETE request."""
        return self._request("DELETE", endpoint, **kwargs)

    # ── Auth endpoints ─────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        """Faz login e salva token."""
        response = self.post("/api/v1/auth/login", data={
            "email": email,
            "password": password,
        })
        self.set_token(
            response.get("access_token", ""),
            response.get("refresh_token"),
        )
        return response

    def register(self, email: str, password: str, full_name: str) -> dict:
        """Registra novo usuário e salva token."""
        response = self.post("/api/v1/auth/register", data={
            "email": email,
            "password": password,
            "full_name": full_name,
        })
        self.set_token(
            response.get("access_token", ""),
            response.get("refresh_token"),
        )
        return response

    def logout(self):
        """Faz logout e limpa token."""
        self.clear_token()

    # ── Bot endpoints ──────────────────────────────────────

    def list_bots(self, page: int = 1, per_page: int = 20) -> dict:
        """Lista bots do usuário."""
        return self.get("/api/v1/bots", params={"page": page, "per_page": per_page})

    def get_bot(self, bot_id: str) -> dict:
        """Obtém detalhes de um bot."""
        return self.get(f"/api/v1/bots/{bot_id}")

    def create_bot(self, name: str, description: str = "", personality: str = "",
                   welcome_message: str = "", **kwargs) -> dict:
        """Cria um novo bot."""
        data = {
            "name": name,
            "description": description,
            "personality": personality,
            "welcome_message": welcome_message,
        }
        data.update(kwargs)
        return self.post("/api/v1/bots", data=data)

    def update_bot(self, bot_id: str, **kwargs) -> dict:
        """Atualiza um bot."""
        return self.put(f"/api/v1/bots/{bot_id}", data=kwargs)

    def delete_bot(self, bot_id: str) -> dict:
        """Deleta um bot."""
        return self.delete(f"/api/v1/bots/{bot_id}")

    def get_bot_stats(self, bot_id: str) -> dict:
        """Obtém estatísticas de um bot."""
        return self.get(f"/api/v1/bots/{bot_id}/stats")

    # ── Chat endpoints ─────────────────────────────────────

    def send_message(self, bot_id: str, message: str, session_id: Optional[str] = None) -> dict:
        """Envia mensagem para um bot."""
        data = {"bot_id": bot_id, "message": message}
        if session_id:
            data["session_id"] = session_id
        return self.post("/api/v1/chat/send", data=data)

    def get_chat_history(self, bot_id: str, session_id: Optional[str] = None, limit: int = 50) -> dict:
        """Obtém histórico de chat."""
        params = {"limit": limit}
        if session_id:
            params["session_id"] = session_id
        return self.get(f"/api/v1/chat/history/{bot_id}", params=params)

    def reset_chat_session(self, bot_id: str, session_id: str) -> dict:
        """Reseta sessão de chat."""
        return self.post(f"/api/v1/chat/reset/{bot_id}", data={"session_id": session_id})

    # ── Flora AI endpoints ─────────────────────────────────

    def flora_chat(self, bot_id: str, message: str, session_id: Optional[str] = None) -> dict:
        """Conversa com Flora AI."""
        data = {"bot_id": bot_id, "message": message}
        if session_id:
            data["session_id"] = session_id
        return self.post("/api/v1/flora/chat", data=data)

    def flora_sessions(self, bot_id: str) -> dict:
        """Lista sessões Flora."""
        return self.get("/api/v1/flora/sessions", params={"bot_id": bot_id})

    # ── WhatsApp endpoints ─────────────────────────────────

    def whatsapp_sessions(self, bot_id: str) -> dict:
        """Lista sessões WhatsApp."""
        return self.get("/api/v1/whatsapp/sessions", params={"bot_id": bot_id})

    def whatsapp_connect(self, bot_id: str) -> dict:
        """Inicia conexão WhatsApp (gera QR Code)."""
        return self.post("/api/v1/whatsapp/sessions", data={"bot_id": bot_id})

    def whatsapp_qr(self, session_id: str) -> dict:
        """Obtém QR Code."""
        return self.get(f"/api/v1/whatsapp/sessions/{session_id}/qr")

    def whatsapp_status(self, session_id: str) -> dict:
        """Obtém status da conexão."""
        return self.get(f"/api/v1/whatsapp/sessions/{session_id}")

    def whatsapp_disconnect(self, session_id: str) -> dict:
        """Desconecta WhatsApp."""
        return self.post(f"/api/v1/whatsapp/sessions/{session_id}/disconnect")

    # ── License endpoints ──────────────────────────────────

    def activate_license(self, license_key: str) -> dict:
        """Ativa uma licença."""
        return self.post("/api/v1/licenses/activate", data={"license_key": license_key})

    def validate_license(self, license_id: str) -> dict:
        """Valida uma licença."""
        return self.get(f"/api/v1/licenses/{license_id}/validate")

    def list_licenses(self) -> dict:
        """Lista licenças do usuário."""
        return self.get("/api/v1/licenses")

    # ── Plans endpoints ────────────────────────────────────

    def list_plans(self) -> dict:
        """Lista planos disponíveis."""
        return self.get("/api/v1/plans")

    def get_plan(self, plan_id: str) -> dict:
        """Obtém detalhes de um plano."""
        return self.get(f"/api/v1/plans/{plan_id}")

    # ── User endpoints ─────────────────────────────────────

    def get_profile(self) -> dict:
        """Obtém perfil do usuário."""
        return self.get("/api/v1/users/me")

    def update_profile(self, **kwargs) -> dict:
        """Atualiza perfil."""
        return self.put("/api/v1/users/me", data=kwargs)

    def get_usage(self) -> dict:
        """Obtém estatísticas de uso."""
        return self.get("/api/v1/users/me/usage")

    # ── Commands endpoints ─────────────────────────────────

    def list_commands(self, bot_id: str) -> dict:
        """Lista comandos de um bot."""
        return self.get("/api/v1/commands", params={"bot_id": bot_id})

    def create_command(self, bot_id: str, name: str, trigger: str, response: str, **kwargs) -> dict:
        """Cria um comando."""
        data = {"bot_id": bot_id, "name": name, "trigger": trigger, "response": response}
        data.update(kwargs)
        return self.post("/api/v1/commands", data=data)

    def update_command(self, command_id: str, **kwargs) -> dict:
        """Atualiza um comando."""
        return self.put(f"/api/v1/commands/{command_id}", data=kwargs)

    def delete_command(self, command_id: str) -> dict:
        """Deleta um comando."""
        return self.delete(f"/api/v1/commands/{command_id}")

    # ── Intents endpoints ──────────────────────────────────

    def list_intents(self, bot_id: str) -> dict:
        """Lista intents de um bot."""
        return self.get("/api/v1/intents", params={"bot_id": bot_id})

    def create_intent(self, bot_id: str, name: str, training_phrases: list, responses: list, **kwargs) -> dict:
        """Cria um intent."""
        data = {
            "bot_id": bot_id,
            "name": name,
            "training_phrases": training_phrases,
            "responses": responses,
        }
        data.update(kwargs)
        return self.post("/api/v1/intents", data=data)

    def classify_intent(self, bot_id: str, text: str) -> dict:
        """Classifica texto contra intents."""
        return self.post("/api/v1/intents/classify", data={"bot_id": bot_id, "text": text})


# Instância global do API Client
api_client = APIClient(
    base_url="http://localhost:8000",
    timeout=30,
    max_retries=3,
)
