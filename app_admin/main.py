"""
Flora Admin Panel — Entry-point application.

A dark-themed, premium admin dashboard built with KivyMD that connects
to the Flora Platform FastAPI backend via REST endpoints.
"""

import asyncio
import json
import threading
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from kivy.config import Config
Config.set("graphics", "width", "1280")
Config.set("graphics", "height", "720")
Config.set("graphics", "minimum_width", "960")
Config.set("graphics", "minimum_height", "600")

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty, ObjectProperty, DictProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton
from kivymd.uix.snackbar import MDSnackbar

from app_admin.styles.theme import Colors, Theme
from app_admin.utils.constants import API, BASE_URL
from app_admin.components.sidebar import SideBar
from app_admin.components.top_bar import TopBar
from app_admin.screens import (
    LoginScreen,
    DashboardScreen,
    BotsScreen,
    LicensesScreen,
    UsersScreen,
    PlansScreen,
    AnalyticsScreen,
    SettingsScreen,
    BotCreateScreen,
)


class APIClient:
    """Lightweight synchronous HTTP client that hits the FastAPI backend."""

    def __init__(self):
        self._token: str | None = None

    # ── token management ────────────────────────────────────────────────
    @property
    def token(self) -> str | None:
        return self._token

    @token.setter
    def token(self, value: str | None):
        self._token = value

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None and len(self._token) > 0

    # ── low-level request helper ───────────────────────────────────────
    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        auth: bool = True,
    ) -> dict:
        url = BASE_URL + path
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"}
        if auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        req = Request(url, data=data, headers=headers, method=method)

        try:
            with urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as e:
            raw = e.read().decode("utf-8")
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {"detail": str(e)}
            raise APIError(e.code, payload.get("detail", str(e)), payload)
        except URLError as e:
            raise APIError(0, f"Servidor indisponível: {e.reason}", {})
        except Exception as e:
            raise APIError(0, str(e), {})

    # ── public endpoints ────────────────────────────────────────────────
    def login(self, email: str, password: str) -> dict:
        resp = self._request("POST", API.LOGIN, {"email": email, "password": password}, auth=False)
        token = resp.get("access_token", "")
        if token:
            self._token = token
        return resp

    # ── admin dashboard ─────────────────────────────────────────────────
    def get_admin_dashboard(self) -> dict:
        return self._request("GET", API.ADMIN_DASHBOARD)

    # ── admin users ─────────────────────────────────────────────────────
    def admin_list_users(self, page: int = 1, page_size: int = 20) -> dict:
        return self._request("GET", f"{API.ADMIN_USERS}?page={page}&page_size={page_size}")

    def admin_update_user(self, user_id: str, body: dict) -> dict:
        return self._request("PUT", API.ADMIN_USER.format(user_id=user_id), body)

    def admin_deactivate_user(self, user_id: str) -> dict:
        return self._request("POST", f"{API.ADMIN_USER.format(user_id=user_id)}/deactivate")

    # ── admin bots ──────────────────────────────────────────────────────
    def admin_list_bots(self, page: int = 1, page_size: int = 20) -> dict:
        return self._request("GET", f"{API.ADMIN_BOTS}?page={page}&page_size={page_size}")

    def admin_deactivate_bot(self, bot_id: str) -> dict:
        return self._request("POST", f"{API.ADMIN_BOTS}/{bot_id}/deactivate")

    # ── admin licenses ──────────────────────────────────────────────────
    def admin_list_licenses(self, page: int = 1, page_size: int = 20) -> dict:
        return self._request("GET", f"{API.ADMIN_LICENSES}?page={page}&page_size={page_size}")

    def admin_revoke_license(self, license_id: str) -> dict:
        return self._request("POST", f"{API.ADMIN_LICENSES}/{license_id}/revoke")

    def admin_create_license(self, body: dict) -> dict:
        return self._request("POST", API.ADMIN_LICENSES, body)

    # ── plans (read-only for admin display) ─────────────────────────────
    def list_plans(self) -> dict:
        return self._request("GET", API.PLANS, auth=False)

    def admin_list_events(self, limit: int = 50) -> dict:
        return self._request("GET", f"{API.ADMIN_EVENTS}?limit={limit}")

    # ── analytics ───────────────────────────────────────────────────────
    def get_analytics_dashboard(self) -> dict:
        return self._request("GET", API.ANALYTICS_DASHBOARD)

    def get_llm_usage(self) -> dict:
        return self._request("GET", API.ANALYTICS_LLM_USAGE)


class APIError(Exception):
    def __init__(self, status_code: int, detail: str, payload: dict):
        self.status_code = status_code
        self.detail = detail
        self.payload = payload
        super().__init__(detail)


class MainScreen(MDScreen):
    """Shell screen: sidebar + topbar + screen manager."""

    def __init__(self, app: "FloraAdminApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation="horizontal")

        # Sidebar
        self.sidebar = SideBar()
        self.sidebar.on_navigate = self._on_navigate
        root.add_widget(self.sidebar)

        # Right panel
        right = MDBoxLayout(orientation="vertical", spacing=0)

        # Top bar
        self.topbar = TopBar(page_title="Dashboard", admin_name="Admin")
        self.topbar.on_logout = self._on_logout
        right.add_widget(self.topbar)

        # Screen manager
        self.screen_manager = MDScreenManager()
        self._screens: dict[str, MDScreen] = {}

        screen_defs = [
            ("dashboard",   DashboardScreen),
            ("bots",        BotsScreen),
            ("licenses",    LicensesScreen),
            ("users",       UsersScreen),
            ("plans",       PlansScreen),
            ("analytics",   AnalyticsScreen),
            ("settings",    SettingsScreen),
            ("bot_create",  BotCreateScreen),
        ]
        for name, cls in screen_defs:
            screen = cls(app=self._app)
            screen.name = name
            self._screens[name] = screen
            self.screen_manager.add_widget(screen)

        right.add_widget(self.screen_manager)
        root.add_widget(right)
        self.add_widget(root)

        # Default screen
        self._on_navigate("dashboard")

    # ── navigation ───────────────────────────────────────────────────────
    TITLE_MAP = {
        "dashboard":  "Dashboard",
        "bots":       "Bots",
        "licenses":   "Licenças",
        "users":      "Usuários",
        "plans":      "Planos",
        "analytics":  "Analytics",
        "settings":   "Configurações",
        "bot_create": "Novo Bot",
    }

    def _on_navigate(self, screen_name: str):
        screen = self._screens.get(screen_name)
        if screen is None:
            return
        self.screen_manager.current = screen_name
        title = self.TITLE_MAP.get(screen_name, screen_name)
        self.topbar.page_title = title
        self.sidebar.current_screen = screen_name

        # Refresh data when switching
        if hasattr(screen, "load_data"):
            screen.load_data()

    def _on_logout(self):
        self._app.logout()


class FloraAdminApp(MDApp):
    """Root KivyMD application."""

    admin_name = StringProperty("Admin")
    token = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Dark"
        self.api = APIClient()
        self._main_screen: MainScreen | None = None

    def build(self):
        Window.clearcolor = Colors.BG_BASE
        return LoginScreen(app=self)

    # ── auth helpers ─────────────────────────────────────────────────────
    def login(self, email: str, password: str) -> bool:
        try:
            resp = self.api.login(email, password)
            self.token = resp.get("access_token", "")
            user = resp.get("user", {})
            self.admin_name = user.get("name", "Admin")
            return True
        except APIError:
            return False
        except Exception:
            return False

    def on_login_success(self):
        """Replace root widget with main shell after successful login."""
        self.root.clear_widgets()
        self._main_screen = MainScreen(app=self)
        self._main_screen.topbar.admin_name = self.admin_name
        self.root.add_widget(self._main_screen)

    def logout(self):
        self.api.token = None
        self.token = ""
        self.admin_name = "Admin"
        self.root.clear_widgets()
        self.root.add_widget(LoginScreen(app=self))

    # ── snackbar helper ─────────────────────────────────────────────────
    def show_snackbar(self, text: str, bg_color=None):
        color = bg_color or (*Colors.PRIMARY[:3], 1)
        MDSnackbar(
            MDLabel(
                text=text,
                theme_text_color="Custom",
                text_color=Colors.WHITE,
            ),
            md_bg_color=color,
            pos_hint={"center_x": 0.5},
            size_hint_x=0.5,
        ).open()
