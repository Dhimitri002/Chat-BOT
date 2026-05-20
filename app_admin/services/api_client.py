"""
API Client for the Flora Admin Panel.
Handles all HTTP communication with the FastAPI backend.
"""
import json
import threading
from typing import Any, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from app_admin.utils.constants import (
    API_BASE_URL,
    API_TIMEOUT,
    API_LOGIN,
    API_ME,
    API_REFRESH,
    API_ADMIN_DASHBOARD,
    API_ADMIN_USERS,
    API_ADMIN_BOTS,
    API_ADMIN_LICENSES,
    API_ADMIN_SETTINGS,
    API_ADMIN_BROADCAST,
    API_PLANS,
    API_ANALYTICS,
)


class APIError(Exception):
    """Custom API error exception."""

    def __init__(self, status_code: int, message: str, detail: Any = None):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(f"API Error {status_code}: {message}")


class APIClient:
    """HTTP client for the Flora Platform API."""

    def __init__(self):
        self.base_url = API_BASE_URL
        self.timeout = API_TIMEOUT
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    def set_token(self, token: str, refresh_token: str = ""):
        """Set the auth token."""
        self._token = token
        self._refresh_token = refresh_token

    def clear_token(self):
        """Clear auth tokens."""
        self._token = None
        self._refresh_token = None

    def _build_url(self, endpoint: str, params: Optional[dict] = None) -> str:
        """Build full URL with optional query params."""
        url = f"{self.base_url}{endpoint}"
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url += "?" + urlencode(filtered)
        return url

    def _get_headers(self, include_auth: bool = True) -> dict:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if include_auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        include_auth: bool = True,
    ) -> dict:
        """Make an HTTP request and return parsed JSON response."""
        url = self._build_url(endpoint, params)
        body = json.dumps(data).encode("utf-8") if data else None
        headers = self._get_headers(include_auth)

        req = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(req, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
                if response_body:
                    return json.loads(response_body)
                return {}
        except HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            try:
                error_data = json.loads(error_body)
                message = error_data.get("detail", str(e))
            except (json.JSONDecodeError, ValueError):
                message = error_body or str(e)
            raise APIError(e.code, message)
        except URLError as e:
            raise APIError(0, f"Erro de conexao: {e.reason}")
        except Exception as e:
            raise APIError(0, f"Erro inesperado: {str(e)}")

    def _request_async(
        self,
        method: str,
        endpoint: str,
        callback,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        include_auth: bool = True,
    ):
        """Make an async HTTP request in a background thread."""
        def _run():
            try:
                result = self._request(method, endpoint, data, params, include_auth)
                if callback:
                    callback(result, None)
            except APIError as e:
                if callback:
                    callback(None, e)
            except Exception as e:
                if callback:
                    callback(None, APIError(0, str(e)))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    # ==================== Auth ====================

    def login(self, email: str, password: str) -> dict:
        """Authenticate and store tokens."""
        result = self._request("POST", API_LOGIN, data={"email": email, "password": password}, include_auth=False)
        if result.get("access_token"):
            self.set_token(
                result["access_token"],
                result.get("refresh_token", ""),
            )
        return result

    def get_current_user(self) -> dict:
        """Get current authenticated user info."""
        return self._request("GET", API_ME)

    def refresh_token(self) -> dict:
        """Refresh the access token."""
        if not self._refresh_token:
            raise APIError(401, "Sem token de atualizacao")
        result = self._request(
            "POST",
            API_REFRESH,
            data={"refresh_token": self._refresh_token},
            include_auth=False,
        )
        if result.get("access_token"):
            self._token = result["access_token"]
            if result.get("refresh_token"):
                self._refresh_token = result["refresh_token"]
        return result

    def login_async(self, email: str, password: str, callback=None):
        """Async login."""
        self._request_async("POST", API_LOGIN, callback, data={"email": email, "password": password}, include_auth=False)

    # ==================== Dashboard ====================

    def get_dashboard(self) -> dict:
        """Get admin dashboard data."""
        return self._request("GET", API_ADMIN_DASHBOARD)

    def get_dashboard_async(self, callback=None):
        """Async dashboard fetch."""
        self._request_async("GET", API_ADMIN_DASHBOARD, callback)

    # ==================== Users ====================

    def get_users(self, page: int = 1, per_page: int = 20, search: str = "", status: str = "") -> dict:
        """Get list of users."""
        params = {"page": page, "per_page": per_page}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        return self._request("GET", API_ADMIN_USERS, params=params)

    def get_user(self, user_id: str) -> dict:
        """Get single user details."""
        return self._request("GET", f"{API_ADMIN_USERS}/{user_id}")

    def update_user(self, user_id: str, data: dict) -> dict:
        """Update user data."""
        return self._request("PUT", f"{API_ADMIN_USERS}/{user_id}", data=data)

    def delete_user(self, user_id: str) -> dict:
        """Delete a user."""
        return self._request("DELETE", f"{API_ADMIN_USERS}/{user_id}")

    def ban_user(self, user_id: str) -> dict:
        """Ban a user."""
        return self._request("POST", f"{API_ADMIN_USERS}/{user_id}/ban")

    def unban_user(self, user_id: str) -> dict:
        """Unban a user."""
        return self._request("POST", f"{API_ADMIN_USERS}/{user_id}/unban")

    def get_users_async(self, callback, page: int = 1, per_page: int = 20, search: str = "", status: str = ""):
        """Async users fetch."""
        params = {"page": page, "per_page": per_page}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        self._request_async("GET", API_ADMIN_USERS, callback, params=params)

    # ==================== Bots ====================

    def get_bots(self, page: int = 1, per_page: int = 20, search: str = "", status: str = "") -> dict:
        """Get list of all bots."""
        params = {"page": page, "per_page": per_page}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        return self._request("GET", API_ADMIN_BOTS, params=params)

    def get_bot(self, bot_id: str) -> dict:
        """Get single bot details."""
        return self._request("GET", f"{API_ADMIN_BOTS}/{bot_id}")

    def pause_bot(self, bot_id: str) -> dict:
        """Pause a bot."""
        return self._request("POST", f"{API_ADMIN_BOTS}/{bot_id}/pause")

    def resume_bot(self, bot_id: str) -> dict:
        """Resume a bot."""
        return self._request("POST", f"{API_ADMIN_BOTS}/{bot_id}/resume")

    def delete_bot(self, bot_id: str) -> dict:
        """Delete a bot."""
        return self._request("DELETE", f"{API_ADMIN_BOTS}/{bot_id}")

    def get_bots_async(self, callback, page: int = 1, per_page: int = 20, search: str = "", status: str = ""):
        """Async bots fetch."""
        params = {"page": page, "per_page": per_page}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        self._request_async("GET", API_ADMIN_BOTS, callback, params=params)

    # ==================== Plans ====================

    def get_plans(self) -> dict:
        """Get all plans."""
        return self._request("GET", API_PLANS, params={"include_private": "true"})

    def get_plan(self, plan_id: str) -> dict:
        """Get single plan details."""
        return self._request("GET", f"{API_PLANS}/{plan_id}")

    def create_plan(self, data: dict) -> dict:
        """Create a new plan."""
        return self._request("POST", API_PLANS, data=data)

    def update_plan(self, plan_id: str, data: dict) -> dict:
        """Update a plan."""
        return self._request("PUT", f"{API_PLANS}/{plan_id}", data=data)

    def delete_plan(self, plan_id: str) -> dict:
        """Delete a plan."""
        return self._request("DELETE", f"{API_PLANS}/{plan_id}")

    def get_plans_async(self, callback):
        """Async plans fetch."""
        self._request_async("GET", API_PLANS, callback, params={"include_private": "true"})

    # ==================== Licenses ====================

    def get_licenses(self, page: int = 1, per_page: int = 20, search: str = "", status: str = "") -> dict:
        """Get all licenses."""
        params = {"page": page, "per_page": per_page}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        return self._request("GET", API_ADMIN_LICENSES, params=params)

    def get_license(self, license_id: str) -> dict:
        """Get single license details."""
        return self._request("GET", f"{API_ADMIN_LICENSES}/{license_id}")

    def generate_license(self, data: dict) -> dict:
        """Generate a new license key."""
        return self._request("POST", API_ADMIN_LICENSES, data=data)

    def revoke_license(self, license_id: str, reason: str = "") -> dict:
        """Revoke a license."""
        return self._request("POST", f"{API_ADMIN_LICENSES}/{license_id}/revoke", data={"reason": reason})

    def activate_license(self, license_id: str) -> dict:
        """Activate a license."""
        return self._request("POST", f"{API_ADMIN_LICENSES}/{license_id}/activate")

    def get_licenses_async(self, callback, page: int = 1, per_page: int = 20, search: str = "", status: str = ""):
        """Async licenses fetch."""
        params = {"page": page, "per_page": per_page}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        self._request_async("GET", API_ADMIN_LICENSES, callback, params=params)

    # ==================== Analytics ====================

    def get_analytics(self, date_from: str = "", date_to: str = "") -> dict:
        """Get analytics data."""
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        return self._request("GET", API_ANALYTICS, params=params if params else None)

    def get_analytics_async(self, callback, date_from: str = "", date_to: str = ""):
        """Async analytics fetch."""
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        self._request_async("GET", API_ANALYTICS, callback, params=params if params else None)

    # ==================== Settings ====================

    def get_settings(self) -> dict:
        """Get platform settings."""
        return self._request("GET", API_ADMIN_SETTINGS)

    def update_settings(self, data: dict) -> dict:
        """Update platform settings."""
        return self._request("PUT", API_ADMIN_SETTINGS, data=data)

    def get_settings_async(self, callback):
        """Async settings fetch."""
        self._request_async("GET", API_ADMIN_SETTINGS, callback)

    # ==================== Broadcast ====================

    def send_broadcast(self, message: str, target: str = "all") -> dict:
        """Send broadcast message."""
        return self._request("POST", API_ADMIN_BROADCAST, data={"message": message, "target": target})


# Global API client instance
api_client = APIClient()
