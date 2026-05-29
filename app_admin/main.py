"""
Flora Platform — Admin Panel
==============================
Premium dark admin panel for managing the Flora Platform.
Built with KivyMD, FastAPI backend integration, and LLM-powered analytics.
"""

import os
import sys

# Ensure project root is in path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kivy.config import Config
Config.set("graphics", "width", "1280")
Config.set("graphics", "height", "720")
Config.set("graphics", "minimum_width", "960")
Config.set("graphics", "minimum_height", "600")

from kivy.core.window import Window
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.screenmanager import FadeTransition, SlideTransition

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen

# ── Theme imports ──────────────────────────────────────────────────────────
from app_admin.styles.theme import (
    Colors, Theme, Typography, Spacing,
    Radius, Elevation, hex_to_rgba,
)
from app_admin.styles.components import (
    PremiumCard, GradientButton, StatusBadge,
    SearchBar, StatCard, DataTable, ModalDialog,
    AnimatedFAB, SnackbarNotification, SkeletonLoader,
    EmptyState, ProgressBar, Divider,
)

# ── Application imports ────────────────────────────────────────────────────
from app_admin.screens.login_screen import LoginScreen
from app_admin.screens.dashboard_screen import DashboardScreen
from app_admin.screens.users_screen import UsersScreen
from app_admin.screens.bots_screen import BotsScreen
from app_admin.screens.analytics_screen import AnalyticsScreen
from app_admin.screens.settings_screen import SettingsScreen

# ── Additional screens (consolidated from apps/admin/) ──────────────────────
from app_admin.screens.bot_form_screen import BotFormScreen
from app_admin.screens.license_form_screen import LicenseFormScreen
from app_admin.screens.whatsapp_screen import AdminWhatsAppScreen


KV_ADMIN = """
#:import get_color_from_hex kivy.utils.get_color_from_hex
#:import Colors app_admin.styles.theme.Colors
#:import Theme app_admin.styles.theme.Theme

<MDScreenManager>:
    transition: SlideTransition(duration=0.3)

<ContentNavigationDrawer>:
    orientation: "vertical"
    padding: "16dp"
    spacing: "8dp"

    # ── Drawer Header ──────────────────────────────────────────────
    MDBoxLayout:
        orientation: "horizontal"
        size_hint_y: None
        height: "72dp"
        padding: "12dp"
        spacing: "12dp"

        MDIconButton:
            icon: "robot"
            theme_text_color: "Custom"
            text_color: app_admin.styles.theme.Colors.PRIMARY
            user_font_size: "32dp"
            size_hint_x: None
            width: dp(48)

        MDBoxLayout:
            orientation: "vertical"
            spacing: dp(2)

            MDLabel:
                text: "Flora Admin"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: app_admin.styles.theme.Colors.TEXT_PRIMARY
                size_hint_y: None
                height: dp(24)

            MDLabel:
                text: "Painel Administrativo"
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: app_admin.styles.theme.Colors.TEXT_HINT
                size_hint_y: None
                height: dp(16)

    # ── Divider ────────────────────────────────────────────────────
    MDDivider:
        color: app_admin.styles.theme.Colors.BG_HOVER

    # ── Navigation Items ───────────────────────────────────────────
    MDBoxLayout:
        orientation: "vertical"
        spacing: "4dp"
        id: nav_items

        MDIconButton:
            icon: "view-dashboard"
            theme_text_color: "Custom"
            text_color: app_admin.styles.theme.Colors.TEXT_SECONDARY
            on_release: app.switch_screen("dashboard")

        MDIconButton:
            icon: "account-group"
            theme_text_color: "Custom"
            text_color: app_admin.styles.theme.Colors.TEXT_SECONDARY
            on_release: app.switch_screen("users")

        MDIconButton:
            icon: "robot"
            theme_text_color: "Custom"
            text_color: app_admin.styles.theme.Colors.TEXT_SECONDARY
            on_release: app.switch_screen("bots")

        MDIconButton:
            icon: "chart-line"
            theme_text_color: "Custom"
            text_color: app_admin.styles.theme.Colors.TEXT_SECONDARY
            on_release: app.switch_screen("analytics")

    # ── Spacer ─────────────────────────────────────────────────────
    Widget:

    # ── Settings ───────────────────────────────────────────────────
    MDDivider:
        color: app_admin.styles.theme.Colors.BG_HOVER

    MDIconButton:
        icon: "cog"
        theme_text_color: "Custom"
        text_color: app_admin.styles.theme.Colors.TEXT_SECONDARY
        on_release: app.switch_screen("settings")

    MDIconButton:
        icon: "logout"
        theme_text_color: "Custom"
        text_color: app_admin.styles.theme.Colors.ERROR
        on_release: app.logout()
"""


class FloraAdminApp(MDApp):
    """
    Flora Platform Admin Application.
    Premium dark theme with full platform management capabilities.
    """

    # ── App Properties ─────────────────────────────────────────────────────
    title = "Flora Admin"
    api_base_url = StringProperty("http://127.0.0.1:8000")
    _auth_token: str = ""
    _current_user: dict = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Dark"
        self._apply_premium_theme()

    def _apply_premium_theme(self):
        """Apply the premium dark theme to KivyMD theme_cls."""
        tc = self.theme_cls

        # Primary palette — Pink
        tc.primary_palette = "Pink"
        tc.primary_hue = "400"

        # Accent palette — Purple
        tc.accent_palette = "DeepPurple"
        tc.accent_hue = "300"

        # Background colors
        tc.bg_darkest = Colors.BG_BASE
        tc.bg_dark = Colors.BG_SECONDARY
        tc.bg_medium = Colors.BG_CARD
        tc.bg_light = Colors.BG_HOVER

        # Text colors
        tc.text_color = Colors.TEXT_PRIMARY
        tc.secondary_text_color = Colors.TEXT_SECONDARY
        tc.hint_text_color = Colors.TEXT_HINT
        tc.disabled_text_color = Colors.TEXT_DISABLED

        # Opposite text colors
        tc.opposite_text_color = Colors.BG_BASE
        tc.opposite_bg_darkest = Colors.TEXT_PRIMARY
        tc.opposite_bg_dark = Colors.TEXT_PRIMARY
        tc.opposite_bg_medium = Colors.TEXT_SECONDARY
        tc.opposite_bg_light = Colors.TEXT_HINT

        # Divider
        tc.divider_color = Colors.BG_HOVER

        # Opacity
        tc.disabled_primary_color = (*Colors.TEXT_DISABLED[:3], 0.5)

    def build(self):
        """Build the application."""
        Builder.load_string(KV_ADMIN)

        # Set window background
        Window.clearcolor = Colors.BG_BASE

        # Create screen manager with slide transition
        self.screen_manager = MDScreenManager()
        self.screen_manager.transition = SlideTransition(
            duration=0.3, direction="left"
        )

        # Add screens
        self.screen_manager.add_widget(LoginScreen(self, name="login"))
        self.screen_manager.add_widget(DashboardScreen(self, name="dashboard"))
        self.screen_manager.add_widget(UsersScreen(self, name="users"))
        self.screen_manager.add_widget(BotsScreen(self, name="bots"))
        self.screen_manager.add_widget(AnalyticsScreen(self, name="analytics"))
        self.screen_manager.add_widget(SettingsScreen(self, name="settings"))

        # ── Consolidated screens from apps/admin/ ──────────────────────────
        self.screen_manager.add_widget(BotFormScreen(self, name="bot_form"))
        self.screen_manager.add_widget(LicenseFormScreen(self, name="license_form"))
        self.screen_manager.add_widget(AdminWhatsAppScreen(self, name="whatsapp_admin"))

        return self.screen_manager

    def switch_screen(self, screen_name: str, direction: str = "left"):
        """Switch to a different screen with animation."""
        if self.screen_manager.current != screen_name:
            self.screen_manager.transition = SlideTransition(
                duration=0.3, direction=direction
            )
            self.screen_manager.current = screen_name

    def switch_screen_fade(self, screen_name: str):
        """Switch screen with fade transition."""
        if self.screen_manager.current != screen_name:
            self.screen_manager.transition = FadeTransition(duration=0.3)
            self.screen_manager.current = screen_name

    def show_snackbar(self, message: str, snackbar_type: str = "info"):
        """Show a snackbar notification on the current screen."""
        current = self.screen_manager.current_screen
        if current:
            SnackbarNotification.show(current, message, snackbar_type)

    def show_loading(self, parent, count: int = 3) -> SkeletonLoader:
        """Show a skeleton loader."""
        loader = SkeletonLoader(count=count)
        parent.add_widget(loader)
        return loader

    def hide_loading(self, loader: SkeletonLoader):
        """Hide a skeleton loader."""
        if loader and loader.parent:
            loader.parent.remove_widget(loader)

    def show_modal(self, title: str, text: str, on_confirm=None, on_cancel=None):
        """Show a modal dialog."""
        modal = ModalDialog(
            title=title,
            text=text,
            on_confirm=on_confirm,
            on_cancel=on_cancel,
        )
        modal.open()

    def set_auth_token(self, token: str):
        """Set the authentication token."""
        self._auth_token = token

    def get_auth_token(self) -> str:
        """Get the current authentication token."""
        return self._auth_token

    def set_current_user(self, user: dict):
        """Set the current user data."""
        self._current_user = user

    def get_current_user(self) -> dict:
        """Get the current user data."""
        return self._current_user

    def logout(self):
        """Log out and return to login screen."""
        self._auth_token = ""
        self._current_user = {}
        self.switch_screen_fade("login")

    def on_start(self):
        """Called when the app starts."""
        pass


if __name__ == "__main__":
    FloraAdminApp().run()
