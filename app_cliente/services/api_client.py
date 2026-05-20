"""API Client - Cliente HTTP para comunicação com o backend."""
import json
import os
from typing import Any, Optional

from kivy.app import MDApp


class APIClient:
    """Cliente HTTP para a API do backend."""

    def __init__(self):
        app = MDApp.get_running_app()
        self.base_url = getattr(app, "api_base_url", "http://localhost:8000/api/v1")
        self._token: Optional[str] = None

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        token = self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _get_token(self) -> Optional[str]:
        if not self._token:
            from app_cliente.services.auth import AuthService
            self._get_token = lambda: AuthService().get_token()
            self._token = self._get_token()
        return self._token

    def _request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Faz requisição HTTP."""
        import urllib.request
        import urllib.error

        url = f"{self.base_url}{endpoint}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"

        try:
            body = json.dumps(data).encode() if data else None
            req = urllib.request.Request(url, data=body, headers=self._get_headers(), method=method)

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                return {"success": True, **result}
        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode())
                return {"success": False, "error": error_body.get("detail", str(e))}
            except Exception:
                return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get(self, endpoint: str, params: dict = None) -> dict:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: dict = None) -> dict:
        return self._request("POST", endpoint, data=data)

    def put(self, endpoint: str, data: dict = None) -> dict:
        return self._request("PUT", endpoint, data=data)

    def delete(self, endpoint: str) -> dict:
        return self._request("DELETE", endpoint)

    # --- Auth ---

    def login(self, email: str, password: str) -> dict:
        return self.post("/auth/login", {"email": email, "password": password})

    def register(self, name: str, email: str, password: str) -> dict:
        return self.post("/auth/register", {"full_name": name, "email": email, "password": password})

    # --- Bots ---

    def get_bots(self) -> dict:
        return self.get("/bots/")

    def get_bot(self, bot_id: str) -> dict:
        return self.get(f"/bots/{bot_id}")

    def create_bot(self, **kwargs) -> dict:
        return self.post("/bots/", kwargs)

    def update_bot(self, bot_id: str, **kwargs) -> dict:
        return self.put(f"/bots/{bot_id}", kwargs)

    def delete_bot(self, bot_id: str) -> dict:
        return self.delete(f"/bots/{bot_id}")

    # --- WhatsApp ---

    def connect_whatsapp(self, bot_id: str) -> dict:
        return self.post(f"/whatsapp/connect/{bot_id}")

    def disconnect_whatsapp(self, bot_id: str) -> dict:
        return self.post(f"/whatsapp/disconnect/{bot_id}")

    def get_whatsapp_status(self, bot_id: str) -> dict:
        return self.get(f"/whatsapp/status/{bot_id}")

    def get_qr_code(self, bot_id: str) -> dict:
        return self.get(f"/whatsapp/qr/{bot_id}")

    def send_message(self, bot_id: str, to: str, text: str) -> dict:
        return self.post(f"/whatsapp/send/{bot_id}", {"to": to, "text": text})

    # --- Chat ---

    def get_chat_history(self, bot_id: str, page: int = 1) -> dict:
        return self.get(f"/chat/history/{bot_id}", {"page": page})

    def get_conversations(self, bot_id: str) -> dict:
        return self.get(f"/chat/conversations/{bot_id}")

    # --- Flora ---

    def flora_chat(self, bot_id: str, message: str, session_id: str = None) -> dict:
        data = {"bot_id": bot_id, "message": message}
        if session_id:
            data["session_id"] = session_id
        return self.post("/flora/chat", data)

    # --- Plans ---

    def get_plans(self) -> dict:
        return self.get("/plans/")

    # --- Analytics ---

    def get_dashboard(self) -> dict:
        return self.get("/analytics/dashboard")

    # --- User ---

    def get_profile(self) -> dict:
        return self.get("/users/me")

    def update_profile(self, **kwargs) -> dict:
        return self.put("/users/me", kwargs)
