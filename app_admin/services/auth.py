"""
Auth service for the Flora Admin Panel.
Manages authentication state, token storage, and session lifecycle.
"""
import json
import os
from typing import Optional

from app_admin.services.api_client import APIClient, api_client, APIError

# Token storage file path
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".flora_admin_tokens.json")


class AuthService:
    """Manages admin authentication and session state."""

    def __init__(self, client: APIClient = None):
        self.client = client or api_client
        self._current_user: Optional[dict] = None
        self._is_admin: bool = False
        self._load_tokens()

    @property
    def is_authenticated(self) -> bool:
        return self.client.is_authenticated

    @property
    def is_admin(self) -> bool:
        return self._is_admin

    @property
    def current_user(self) -> Optional[dict]:
        return self._current_user

    def _load_tokens(self):
        """Load saved tokens from disk."""
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, "r") as f:
                    data = json.load(f)
                token = data.get("access_token", "")
                refresh = data.get("refresh_token", "")
                if token:
                    self.client.set_token(token, refresh)
        except (json.JSONDecodeError, IOError, KeyError):
            pass

    def _save_tokens(self):
        """Save tokens to disk."""
        try:
            data = {
                "access_token": self.client._token or "",
                "refresh_token": self.client._refresh_token or "",
            }
            with open(TOKEN_FILE, "w") as f:
                json.dump(data, f)
        except IOError:
            pass

    def _clear_tokens(self):
        """Remove saved tokens."""
        try:
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
        except IOError:
            pass

    def login(self, email: str, password: str) -> tuple[bool, str]:
        """
        Attempt to log in with email and password.
        Returns (success, message).
        """
        try:
            result = self.client.login(email, password)
            if result.get("access_token"):
                self._save_tokens()
                # Verify admin role
                try:
                    user_info = self.client.get_current_user()
                    self._current_user = user_info
                    role = user_info.get("role", "user")
                    if role in ("admin", "superadmin"):
                        self._is_admin = True
                        return True, "Login realizado com sucesso!"
                    else:
                        self.logout()
                        return False, "Acesso negado. Permissao de administrador necessaria."
                except APIError:
                    pass
                return True, "Login realizado com sucesso!"
            return False, "Falha na autenticacao."
        except APIError as e:
            if e.status_code == 401:
                return False, "Email ou senha invalidos."
            return False, f"Erro no login: {e.message}"
        except Exception as e:
            return False, f"Erro de conexao: {str(e)}"

    def login_async(self, email: str, password: str, callback=None):
        """
        Async login with callback.
        Callback receives (success, message).
        """
        def _on_result(result, error):
            if error:
                if error.status_code == 401:
                    if callback:
                        callback(False, "Email ou senha invalidos.")
                else:
                    if callback:
                        callback(False, f"Erro no login: {error.message}")
                return

            if result and result.get("access_token"):
                self.client.set_token(
                    result["access_token"],
                    result.get("refresh_token", ""),
                )
                self._save_tokens()
                if callback:
                    callback(True, "Login realizado com sucesso!")
            else:
                if callback:
                    callback(False, "Falha na autenticacao.")

        self.client.login_async(email, password, _on_result)

    def logout(self):
        """Log out and clear all session data."""
        self.client.clear_token()
        self._current_user = None
        self._is_admin = False
        self._clear_tokens()

    def check_session(self) -> bool:
        """Verify if the current session is still valid."""
        if not self.client.is_authenticated:
            return False
        try:
            user_info = self.client.get_current_user()
            self._current_user = user_info
            role = user_info.get("role", "user")
            self._is_admin = role in ("admin", "superadmin")
            return True
        except APIError:
            # Try to refresh token
            try:
                self.client.refresh_token()
                self._save_tokens()
                return True
            except APIError:
                self.logout()
                return False

    def get_user_display_name(self) -> str:
        """Get the display name of the current user."""
        if self._current_user:
            return self._current_user.get("name", "Admin")
        return "Administrador"

    def get_user_email(self) -> str:
        """Get the email of the current user."""
        if self._current_user:
            return self._current_user.get("email", "")
        return ""


# Global auth service instance
auth_service = AuthService()
