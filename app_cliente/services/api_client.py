"""
Flora Platform — API Client
============================
HTTP client for communicating with the FastAPI backend.
Handles authentication, request/response serialization,
and error handling.
"""
import json
import logging
from typing import Optional, Callable
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Raised when an API request fails."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")


class APIClient:
    """HTTP client for the Flora Platform backend API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._current_user: Optional[dict] = None
        self._on_token_refresh: Optional[Callable] = None

    # ─── Properties ────────────────────────────────────────────

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    @property
    def token(self) -> Optional[str]:
        return self._token

    @property
    def current_user(self) -> Optional[dict]:
        return self._current_user

    # ─── Token Management ──────────────────────────────────────

    def set_token(self, token: str):
        self._token = token

    def set_refresh_token(self, token: str):
        self._refresh_token = token

    def clear_auth(self):
        self._token = None
        self._refresh_token = None
        self._current_user = None

    def set_current_user(self, user: dict):
        self._current_user = user

    # ─── Request Methods ───────────────────────────────────────

    def _make_request(
        self,
        method: str,
        path: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        auth: bool = False,
    ) -> dict:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urlencode(params)

        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        request = Request(url, data=body, method=method)
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")

        if auth:
            if not self._token:
                raise APIError(401, "Nao autenticado")
            request.add_header("Authorization", f"Bearer {self._token}")

        try:
            response = urlopen(request, timeout=30)
            raw = response.read()
            if raw:
                return json.loads(raw)
            return {}
        except HTTPError as e:
            raw = e.read()
            try:
                err_data = json.loads(raw)
                detail = err_data.get("detail", str(e))
            except Exception:
                detail = str(e)
            if e.code == 401:
                self.clear_auth()
            raise APIError(e.code, detail)
        except URLError as e:
            logger.error(f"Connection error: {e}")
            raise APIError(0, f"Sem conexao com o servidor: {e.reason}")
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise APIError(0, str(e))

    # ─── Auth Endpoints ────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        """Authenticate with email and password."""
        resp = self._make_request(
            "POST",
            "/api/v1/auth/login",
            data={"email": email, "password": password},
        )
        if resp.get("access_token"):
            self._token = resp["access_token"]
            self._refresh_token = resp.get("refresh_token")
            # The /login endpoint returns user info under "user" key
            if resp.get("user"):
                self._current_user = resp["user"]
            elif resp.get("id"):
                self._current_user = resp
        return resp

    def register(self, email: str, password: str, name: str, license_key: str) -> dict:
        """Register a new user account with a license key."""
        resp = self._make_request(
            "POST",
            "/api/v1/auth/register",
            data={
                "email": email,
                "password": password,
                "name": name,
                "license_key": license_key,
            },
        )
        if resp.get("access_token"):
            self._token = resp["access_token"]
            self._refresh_token = resp.get("refresh_token")
            if resp.get("user"):
                self._current_user = resp["user"]
            elif resp.get("id"):
                self._current_user = resp
        return resp

    def get_profile(self) -> dict:
        """Get the current user's profile."""
        resp = self._make_request("GET", "/api/v1/auth/me", auth=True)
        self._current_user = resp
        return resp

    def refresh_token(self) -> dict:
        """Refresh the access token."""
        if not self._refresh_token:
            raise APIError(401, "Sem token de refresh")
        resp = self._make_request(
            "POST",
            "/api/v1/auth/refresh",
            data={"refresh_token": self._refresh_token},
        )
        if resp.get("access_token"):
            self._token = resp["access_token"]
        return resp

    # ─── Bot Endpoints ─────────────────────────────────────────

    def list_bots(self, page: int = 1, page_size: int = 20) -> dict:
        """List all bots for the current user."""
        return self._make_request(
            "GET",
            "/api/v1/bots",
            params={"page": page, "page_size": page_size},
            auth=True,
        )

    def get_bot(self, bot_id: str) -> dict:
        """Get a specific bot by ID."""
        return self._make_request("GET", f"/api/v1/bots/{bot_id}", auth=True)

    def create_bot(self, data: dict) -> dict:
        """Create a new bot."""
        return self._make_request("POST", "/api/v1/bots", data=data, auth=True)

    def update_bot(self, bot_id: str, data: dict) -> dict:
        """Update a bot's configuration."""
        return self._make_request("PUT", f"/api/v1/bots/{bot_id}", data=data, auth=True)

    def delete_bot(self, bot_id: str) -> dict:
        """Delete a bot."""
        return self._make_request("DELETE", f"/api/v1/bots/{bot_id}", auth=True)

    def activate_bot(self, bot_id: str) -> dict:
        """Activate a bot."""
        return self._make_request("POST", f"/api/v1/bots/{bot_id}/activate", auth=True)

    def deactivate_bot(self, bot_id: str) -> dict:
        """Deactivate a bot."""
        return self._make_request("POST", f"/api/v1/bots/{bot_id}/deactivate", auth=True)

    # ─── Chat Endpoints ────────────────────────────────────────

    def send_message(self, bot_id: str, text: str) -> dict:
        """Send a message to a bot for testing."""
        return self._make_request(
            "POST",
            f"/api/v1/bots/{bot_id}/chat",
            data={"text": text},
            auth=True,
        )

    def get_chat_history(self, bot_id: str, limit: int = 50) -> dict:
        """Get chat history for a bot."""
        return self._make_request(
            "GET",
            f"/api/v1/bots/{bot_id}/chat/history",
            params={"limit": limit},
            auth=True,
        )

    # ─── Flora AI Endpoints ────────────────────────────────────

    def flora_chat(self, message: str, session_id: Optional[str] = None) -> dict:
        """Chat with Flora AI assistant."""
        data = {"message": message}
        if session_id:
            data["session_id"] = session_id
        return self._make_request(
            "POST",
            "/api/v1/flora/chat",
            data=data,
            auth=True,
        )

    # ─── WhatsApp Endpoints ────────────────────────────────────

    def whatsapp_connect(self, bot_id: str) -> dict:
        """Connect a bot to WhatsApp."""
        return self._make_request(
            "POST",
            "/api/v1/whatsapp/connect",
            data={"bot_id": bot_id},
            auth=True,
        )

    def whatsapp_disconnect(self, bot_id: str) -> dict:
        """Disconnect a bot from WhatsApp."""
        return self._make_request(
            "POST",
            "/api/v1/whatsapp/disconnect",
            data={"bot_id": bot_id},
            auth=True,
        )

    def whatsapp_status(self, bot_id: str) -> dict:
        """Get WhatsApp connection status."""
        return self._make_request(
            "GET",
            f"/api/v1/whatsapp/status/{bot_id}",
            auth=True,
        )

    def whatsapp_qr(self, bot_id: str) -> dict:
        """Get WhatsApp QR code."""
        return self._make_request(
            "GET",
            f"/api/v1/whatsapp/qr/{bot_id}",
            auth=True,
        )

    def whatsapp_send(self, bot_id: str, to: str, message: str) -> dict:
        """Send a WhatsApp message."""
        return self._make_request(
            "POST",
            "/api/v1/whatsapp/send",
            data={"bot_id": bot_id, "to": to, "message": message},
            auth=True,
        )

    # ─── Plans Endpoints ───────────────────────────────────────

    def list_plans(self) -> list:
        """List all available plans."""
        return self._make_request("GET", "/api/v1/plans")

    # ─── License Endpoints ─────────────────────────────────────

    def validate_license(self, license_key: str) -> dict:
        """Validate a license key."""
        return self._make_request(
            "POST",
            "/api/v1/licenses/validate",
            data={"license_key": license_key},
        )

    # ─── Commands Endpoints ────────────────────────────────────

    def list_commands(self, bot_id: str) -> dict:
        """List all commands for a bot."""
        return self._make_request(
            "GET",
            f"/api/v1/bots/{bot_id}/commands",
            auth=True,
        )

    def create_command(self, bot_id: str, data: dict) -> dict:
        """Create a new command for a bot."""
        return self._make_request(
            "POST",
            f"/api/v1/bots/{bot_id}/commands",
            data=data,
            auth=True,
        )

    def delete_command(self, bot_id: str, command_id: str) -> dict:
        """Delete a command."""
        return self._make_request(
            "DELETE",
            f"/api/v1/bots/{bot_id}/commands/{command_id}",
            auth=True,
        )
