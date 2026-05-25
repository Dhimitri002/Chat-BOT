"""
Flora Platform — Auth Service
==============================
Handles authentication state, token persistence,
and user session management for the client app.
"""
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Token storage file
TOKEN_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".auth_cache.json",
)


class AuthService:
    """Manages authentication state and token persistence."""

    def __init__(self, api_client):
        self.api = api_client
        self._user: Optional[dict] = None
        self._load_cached_auth()

    # ─── Properties ────────────────────────────────────────────

    @property
    def is_authenticated(self) -> bool:
        return self.api.is_authenticated

    @property
    def user(self) -> Optional[dict]:
        if self._user:
            return self._user
        return self.api.current_user

    @property
    def user_name(self) -> str:
        """Get the user's display name."""
        u = self.user
        if u:
            return u.get("name", u.get("email", "Usuario"))
        return "Usuario"

    @property
    def user_email(self) -> str:
        u = self.user
        if u:
            return u.get("email", "")
        return ""

    @property
    def user_role(self) -> str:
        u = self.user
        if u:
            return u.get("role", "user")
        return "user"

    # ─── Auth Actions ──────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        """Login with email and password."""
        resp = self.api.login(email, password)
        self._user = resp.get("user", resp)
        self._save_cached_auth()
        return resp

    def register(self, email: str, password: str, name: str, license_key: str) -> dict:
        """Register a new account."""
        resp = self.api.register(email, password, name, license_key)
        self._user = resp.get("user", resp)
        self._save_cached_auth()
        return resp

    def logout(self):
        """Logout and clear all auth state."""
        self.api.clear_auth()
        self._user = None
        self._clear_cached_auth()

    def refresh_session(self) -> bool:
        """Try to refresh the session using cached tokens."""
        try:
            self.api.refresh_token()
            self.api.get_profile()
            self._user = self.api.current_user
            self._save_cached_auth()
            return True
        except Exception as e:
            logger.warning(f"Session refresh failed: {e}")
            self.logout()
            return False

    def check_auth(self) -> bool:
        """Check if the current session is valid."""
        if not self.api.is_authenticated:
            return False
        try:
            self.api.get_profile()
            self._user = self.api.current_user
            return True
        except Exception:
            return False

    # ─── Token Persistence ─────────────────────────────────────

    def _save_cached_auth(self):
        """Save auth tokens to local cache."""
        try:
            data = {
                "token": self.api.token,
                "refresh_token": self.api._refresh_token,
                "user": self._user,
            }
            with open(TOKEN_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to save auth cache: {e}")

    def _load_cached_auth(self):
        """Load auth tokens from local cache."""
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, "r") as f:
                    data = json.load(f)
                if data.get("token"):
                    self.api.set_token(data["token"])
                if data.get("refresh_token"):
                    self.api.set_refresh_token(data["refresh_token"])
                if data.get("user"):
                    self._user = data["user"]
                    self.api.set_current_user(data["user"])
        except Exception as e:
            logger.warning(f"Failed to load auth cache: {e}")

    def _clear_cached_auth(self):
        """Remove cached auth tokens."""
        try:
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
        except Exception:
            pass
