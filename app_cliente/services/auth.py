"""Auth Service — Serviço de autenticação com validação de licença online."""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

AUTH_FILE = Path.home() / ".flora_cliente" / "auth.json"
LICENSE_CACHE_FILE = Path.home() / ".flora_cliente" / "license_cache.json"

# TTL do cache de licença (24 horas)
LICENSE_CACHE_TTL = 86400


class AuthService:
    """Gerencia autenticação e licença do cliente."""

    def __init__(self):
        AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)

    # ── Persistência local ─────────────────────────────────

    def _load_json(self, filepath: Path) -> dict:
        """Carrega JSON de um arquivo."""
        if filepath.exists():
            try:
                data = json.loads(filepath.read_text())
                return data if isinstance(data, dict) else {}
            except Exception:
                pass
        return {}

    def _save_json(self, filepath: Path, data: dict):
        """Salva JSON em um arquivo."""
        filepath.write_text(json.dumps(data, indent=2, default=str))

    # ── Tokens ─────────────────────────────────────────────

    def save_token(self, token: str, refresh_token: str = "", expires_in: int = 1800):
        """Salva tokens de autenticação."""
        data = self._load_json(AUTH_FILE)
        data["token"] = token
        data["refresh_token"] = refresh_token
        data["token_created_at"] = datetime.utcnow().isoformat()
        data["token_expires_at"] = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        self._save_json(AUTH_FILE, data)

    def get_token(self) -> Optional[str]:
        """Obtém token de acesso."""
        return self._load_json(AUTH_FILE).get("token")

    def get_refresh_token(self) -> Optional[str]:
        """Obtém refresh token."""
        return self._load_json(AUTH_FILE).get("refresh_token")

    def is_token_expired(self) -> bool:
        """Verifica se o token expirou."""
        data = self._load_json(AUTH_FILE)
        expires_at_str = data.get("token_expires_at")
        if not expires_at_str:
            return True
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            return datetime.utcnow() >= expires_at
        except Exception:
            return True

    def save_user(self, user: dict):
        """Salva dados do usuário."""
        data = self._load_json(AUTH_FILE)
        data["user"] = user
        self._save_json(AUTH_FILE, data)

    def get_user(self) -> Optional[dict]:
        """Obtém dados do usuário."""
        return self._load_json(AUTH_FILE).get("user")

    def logout(self):
        """Faz logout e limpa todos os dados."""
        if AUTH_FILE.exists():
            AUTH_FILE.unlink()
        if LICENSE_CACHE_FILE.exists():
            LICENSE_CACHE_FILE.unlink()

    def is_authenticated(self) -> bool:
        """Verifica se há token válido."""
        token = self.get_token()
        return bool(token and not self.is_token_expired())

    # ── Licença ────────────────────────────────────────────

    def save_license_info(self, license_info: dict):
        """Salva informações da licença em cache."""
        license_info["cached_at"] = datetime.utcnow().isoformat()
        self._save_json(LICENSE_CACHE_FILE, license_info)

    def get_cached_license(self) -> Optional[dict]:
        """Obtém licença do cache (se não expirou)."""
        data = self._load_json(LICENSE_CACHE_FILE)
        if not data:
            return None

        cached_at_str = data.get("cached_at")
        if cached_at_str:
            try:
                cached_at = datetime.fromisoformat(cached_at_str)
                if datetime.utcnow() - cached_at > timedelta(seconds=LICENSE_CACHE_TTL):
                    return None  # Cache expirou
            except Exception:
                pass

        return data

    def is_license_valid(self) -> bool:
        """Verifica se a licença em cache é válida."""
        license_info = self.get_cached_license()
        if not license_info:
            return False
        return license_info.get("valid", False)

    def get_license_features(self) -> dict:
        """Obtém features disponíveis pela licença."""
        license_info = self.get_cached_license()
        if not license_info:
            return {
                "has_access": False,
                "plan": "none",
                "max_bots": 0,
                "max_messages": 0,
                "has_llm": False,
                "has_flora": False,
            }
        return license_info.get("features", {})

    # ── Validação online ───────────────────────────────────

    async def validate_license_online(self, api_client) -> dict:
        """
        Valida licença com o servidor.

        Args:
            api_client: Instância do APIClient

        Returns:
            dict com resultado da validação
        """
        try:
            licenses = api_client.list_licenses()
            if licenses and licenses.get("items"):
                # Pegar primeira licença ativa
                for lic in licenses["items"]:
                    if lic.get("status") == "active":
                        # Validar
                        validation = api_client.validate_license(lic["id"])
                        if validation.get("valid"):
                            # Buscar features do plano
                            features = await self._fetch_license_features(api_client)
                            license_data = {
                                "valid": True,
                                "license_id": lic["id"],
                                "plan_id": lic.get("plan_id"),
                                "plan_name": validation.get("plan_name", "Unknown"),
                                "expires_at": lic.get("expires_at"),
                                "days_remaining": validation.get("days_remaining", 0),
                                "features": features,
                            }
                            self.save_license_info(license_data)
                            return license_data

            return {"valid": False, "reason": "no_active_license"}

        except Exception as e:
            # Se falhar, usar cache
            cached = self.get_cached_license()
            if cached:
                return cached
            return {"valid": False, "reason": str(e)}

    async def _fetch_license_features(self, api_client) -> dict:
        """Busca features da licença."""
        try:
            profile = api_client.get_profile()
            if profile:
                from app_cliente.services.api_client import api_client as client
                # Features vêm do plano ativo
                return profile.get("features", {})
        except Exception:
            pass
        return {}

    # ── Login completo ─────────────────────────────────────

    async def login(self, api_client, email: str, password: str) -> dict:
        """
        Faz login completo: autentica + busca licença.

        Args:
            api_client: Instância do APIClient
            email: Email do usuário
            password: Senha

        Returns:
            dict com resultado do login
        """
        try:
            # 1. Autenticar
            auth_result = api_client.login(email=email, password=password)

            # 2. Salvar tokens
            self.save_token(
                token=auth_result.get("access_token", ""),
                refresh_token=auth_result.get("refresh_token", ""),
                expires_in=auth_result.get("expires_in", 1800),
            )

            # 3. Buscar perfil
            try:
                profile = api_client.get_profile()
                if profile:
                    self.save_user(profile)
            except Exception:
                pass

            # 4. Validar licença
            license_result = await self.validate_license_online(api_client)

            return {
                "success": True,
                "authenticated": True,
                "license_valid": license_result.get("valid", False),
                "license": license_result,
                "user": self.get_user(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    # ── Register completo ──────────────────────────────────

    async def register(self, api_client, email: str, password: str, full_name: str) -> dict:
        """
        Registra novo usuário.

        Args:
            api_client: Instância do APIClient
            email: Email
            password: Senha
            full_name: Nome completo

        Returns:
            dict com resultado do registro
        """
        try:
            auth_result = api_client.register(
                email=email,
                password=password,
                full_name=full_name,
            )

            self.save_token(
                token=auth_result.get("access_token", ""),
                refresh_token=auth_result.get("refresh_token", ""),
                expires_in=auth_result.get("expires_in", 1800),
            )

            try:
                profile = api_client.get_profile()
                if profile:
                    self.save_user(profile)
            except Exception:
                pass

            return {
                "success": True,
                "authenticated": True,
                "user": self.get_user(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
