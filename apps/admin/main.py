"""
Flora Platform — App Admin (KivyMD)
====================================
Dashboard administrativo completo para gerenciamento
da plataforma Flora de chatbots licenciados.

Visual: Dashboard premium escuro com rosa/roxo.
"""

import asyncio
import json
import os
from pathlib import Path

from kivy.config import Config
Config.set("graphics", "width", "1200")
Config.set("graphics", "height", "800")
Config.set("graphics", "minimum_width", "900")
Config.set("graphics", "minimum_height", "600")

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ColorProperty, NumericProperty, StringProperty
from kivy.uix.screenmanager import FadeTransition, ScreenManager

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar

from apps.shared.theme import FloraTheme, FloraColors

# Token storage
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
TOKEN_FILE = DATA_DIR / "auth.json"


class AdminApp(MDApp):
    """Aplicativo administrativo da Flora Platform."""

    title = "Flora Admin"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Pink"
        self._token = None
        self._user = None

    def build(self):
        self._apply_colors()
        self.sm = ScreenManager(transition=FadeTransition(duration=0.2))

        # Import screens
        from apps.admin.screens.login_screen import LoginScreen
        from apps.admin.screens.dashboard_screen import DashboardScreen
        from apps.admin.screens.bots_screen import BotsScreen
        from apps.admin.screens.bot_form_screen import BotFormScreen
        from apps.admin.screens.licenses_screen import LicensesScreen
        from apps.admin.screens.license_form_screen import LicenseFormScreen
        from apps.admin.screens.users_screen import UsersScreen
        from apps.admin.screens.plans_screen import PlansScreen
        from apps.admin.screens.analytics_screen import AnalyticsScreen
        from apps.admin.screens.settings_screen import SettingsScreen
        from apps.admin.screens.whatsapp_screen import WhatsappScreen

        # Add screens
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(DashboardScreen(name="dashboard"))
        self.sm.add_widget(BotsScreen(name="bots"))
        self.sm.add_widget(BotFormScreen(name="bot_form"))
        self.sm.add_widget(LicensesScreen(name="licenses"))
        self.sm.add_widget(LicenseFormScreen(name="license_form"))
        self.sm.add_widget(UsersScreen(name="users"))
        self.sm.add_widget(PlansScreen(name="plans"))
        self.sm.add_widget(AnalyticsScreen(name="analytics"))
        self.sm.add_widget(SettingsScreen(name="settings"))
        self.sm.add_widget(WhatsappScreen(name="whatsapp"))

        # Check stored token
        token = self._load_token()
        if token:
            self._token = token
            self.sm.current = "dashboard"
        else:
            self.sm.current = "login"

        return self.sm

    def _apply_colors(self):
        """Aplica cores customizadas do tema Flora."""
        c = FloraColors()
        self.theme_cls.primary_color = c.to_rgba(FloraColors.PRIMARY_PURPLE)
        self.theme_cls.accent_color = c.to_rgba(FloraColors.ACCENT_PINK)

    def _load_token(self) -> str | None:
        """Carrega token armazenado."""
        try:
            if TOKEN_FILE.exists():
                data = json.loads(TOKEN_FILE.read_text())
                return data.get("token")
        except Exception:
            pass
        return None

    def save_token(self, token: str, user: dict = None):
        """Salva token de autenticação."""
        self._token = token
        self._user = user
        TOKEN_FILE.write_text(json.dumps({"token": token, "user": user}))

    def clear_token(self):
        """Remove token armazenado."""
        self._token = None
        self._user = None
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def current_user(self) -> dict | None:
        return self._user

    def switch_screen(self, name: str):
        """Troca de tela com animação."""
        self.sm.current = name

    def logout(self):
        """Faz logout e volta para login."""
        self.clear_token()
        self.sm.current = "login"


if __name__ == "__main__":
    AdminApp().run()
