"""Auth Service - Serviço de autenticação local."""
import json
import os
from pathlib import Path
from typing import Optional


AUTH_FILE = Path.home() / ".flora_cliente" / "auth.json"


class AuthService:
    """Gerencia autenticação local do cliente."""

    def __init__(self):
        AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _load_data(self) -> dict:
        if AUTH_FILE.exists():
            try:
                return json.loads(AUTH_FILE.read_text())
            except Exception:
                pass
        return {}

    def _save_data(self, data: dict):
        AUTH_FILE.write_text(json.dumps(data, indent=2))

    def save_token(self, token: str):
        data = self._load_data()
        data["token"] = token
        self._save_data(data)

    def get_token(self) -> Optional[str]:
        return self._load_data().get("token")

    def save_user(self, user: dict):
        data = self._load_data()
        data["user"] = user
        self._save_data(data)

    def get_user(self) -> Optional[dict]:
        return self._load_data().get("user")

    def logout(self):
        if AUTH_FILE.exists():
            AUTH_FILE.unlink()

    def is_authenticated(self) -> bool:
        return bool(self.get_token())
