"""
Flora Platform — Client App
=============================
Premium dark client app for WhatsApp chatbot management.
Built with KivyMD, warm dark theme with friendlier aesthetic.
"""

import os
import sys

# Ensure project root is in path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kivy.config import Config
Config.set("graphics", "width", "412")
Config.set("graphics", "height", "896")
Config.set("graphics", "minimum_width", "320")
Config.set("graphics", "minimum_height", "568")

from kivy.core.window import Window
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, DictProperty
from kivy.uix.screenmanager import NoTransition, FadeTransition

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.relativelative import MDRelativeLayout

# ── Theme imports ──────────────────────────────────────────────────────────
from app_cliente.styles.theme import (
    Colors, Theme, Typography, Spacing,
    Radius, Elevation, hex_to_rgba,
)
from app_cliente.styles.components import (
    PremiumCard, GradientButton, StatusBadge,
    SearchBar, StatCard, ChatBubble, TypingIndicator,
    EmptyState, ModalDialog, SnackbarNotification,
    SkeletonLoader, ProgressBar, Divider,
)

# ── Application imports ────────────────────────────────────────────────────
from app_cliente.screens.splash_screen import SplashScreen
from app_cliente.screens.login_screen import LoginScreen
from app_cliente.screens.register_screen import RegisterScreen
from app_cliente.screens.home_screen import HomeScreen
from app_cliente.screens.onboarding_screen import OnboardingScreen
from app_cliente.screens.bot_create_screen import BotCreateScreen
from app_cliente.screens.flora_chat_screen import FloraChatScreen

try:
    from app_cliente.services.auth import AuthService
except ImportError:
    AuthService = None

try:
    from app_cliente.services.api_service import ApiService
except ImportError:
    ApiService = None

try:
    from app_cliente.services.flora_service import FloraService
except ImportError:
    FloraService = None


class ThemeColors:
    """
    Expose theme colors for Builder KV strings.
    This is the same pattern used by the existing screens.
    """
    PRIMARY = Colors.BG_BASE
    BG_BASE = Colors.BG_BASE
    BG_CARD = Colors.BG_CARD
    BG_INPUT = Colors.BG_INPUT
    ACCENT = Colors.PRIMARY
    ACCENT2 = Colors.SECONDARY
    TEXT_PRIMARY = Colors.TEXT_PRIMARY
    TEXT_SECONDARY = Colors.TEXT_SECONDARY
    TEXT_HINT = Colors.TEXT_HINT
    SUCCESS = Colors.SUCCESS
    WARNING = Colors.WARNING
    ERROR = Colors.ERROR
    INFO = Colors.INFO


# ── KV Theme Strings ───────────────────────────────────────────────────────
KV_THEME = """
#:import get_color_from_hex kivy.utils.get_color_from_hex
#:import Colors app_cliente.styles.theme.Colors
#:import Theme app_cliente.styles.theme.Theme

<ThemeCard>:
    md_bg_color: Colors.BG_CARD
    radius: [Radius.LG]
    elevation: Elevation.LOW
    padding: ComponentTokens.CARD_PADDING
    adaptive_height: True

<ThemeButton>:
    md_bg_color: Colors.PRIMARY
    text_color: Colors.TEXT_ON_ACCENT
    font_size: Typography.BUTTON
    bold: True
    radius: [ComponentTokens.BUTTON_RADIUS]
    elevation: Elevation.LOW

<ThemeIconButton>:
    icon_color: Colors.PRIMARY
    theme_icon_color: "Custom"

<ThemeLabel>:
    theme_text_color: "Custom"

<ThemeSpinner>:
    color: Colors.PRIMARY
"""


class FloraApp(MDApp):
    """
    Flora Platform Client Application.
    Premium warm dark theme with full platform capabilities.
    """

    # ── App Properties ─────────────────────────────────────────────────────
    title = "Flora"
    api_base_url = StringProperty("http://127.0.0.1:8000")
    auth_token = StringProperty("")
    current_user = DictProperty({})

    # ── Theme colors (exposed via KV) ──────────────────────────────────────
    theme_colors = ThemeColors

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Dark"
        self._apply_premium_theme()

    def _apply_premium_theme(self):
        """Apply the warm premium dark theme to KivyMD theme_cls."""
        tc = self.theme_cls

        # Primary palette — Pink
        tc.primary_palette = "Pink"
        tc.primary_hue = "400"

        # Accent palette — Deep Purple
        tc.accent_palette = "DeepPurple"
        tc.accent_hue = "300"

        # Background — warm dark
        tc.bg_darkest = Colors.BG_BASE
        tc.bg_dark = Colors.BG_SECONDARY
        tc.bg_medium = Colors.BG_CARD
        tc.bg_light = Colors.BG_HOVER

        # Text
        tc.text_color = Colors.TEXT_PRIMARY
        tc.secondary_text_color = Colors.TEXT_SECONDARY
        tc.hint_text_color = Colors.TEXT_HINT
        tc.disabled_text_color = Colors.TEXT_DISABLED

        # Opposite
        tc.opposite_text_color = Colors.BG_BASE
        tc.opposite_bg_darkest = Colors.TEXT_PRIMARY
        tc.opposite_bg_dark = Colors.TEXT_PRIMARY
        tc.opposite_bg_medium = Colors.TEXT_SECONDARY
        tc.opposite_bg_light = Colors.TEXT_HINT

        # Divider
        tc.divider_color = Colors.BG_HOVER

    def build(self):
        """Build the client application."""
        Builder.load_string(KV_THEME)

        # Set window background
        Window.clearcolor = Colors.BG_BASE

        # Screen manager with no transition (controlled per-screen)
        sm = MDScreenManager()
        sm.transition = NoTransition()

        # ── Screens ────────────────────────────────────────────────────
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(OnboardingScreen(name="onboarding"))
        sm.add_widget(BotCreateScreen(name="bot_create"))
        sm.add_widget(FloraChatScreen(name="flora_chat"))

        sm.current = "splash"

        return sm

    # ── Navigation helpers ─────────────────────────────────────────────────
    def navigate(self, screen_name: str, transition: str = "fade"):
        """Navigate to a screen with transition."""
        sm = self.root
        if sm.current == screen_name:
            return

        if transition == "fade":
            sm.transition = FadeTransition(duration=0.3)
        elif transition == "slide":
            from kivy.uix.screenmanager import SlideTransition
            sm.transition = SlideTransition(duration=0.3, direction="left")
        else:
            sm.transition = NoTransition()

        sm.current = screen_name

    def navigate_back(self):
        """Navigate back to the previous screen."""
        back_map = {
            "login": "splash",
            "register": "login",
            "home": "login",
            "onboarding": "home",
            "bot_create": "home",
            "flora_chat": "home",
        }
        current = self.root.current
        if current in back_map:
            self.navigate(back_map[current])

    # ── Notification helpers ───────────────────────────────────────────────
    def show_snackbar(self, message: str, snackbar_type: str = "info"):
        """Show a snackbar notification."""
        current = self.root.current_screen
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

    # ── Theme color accessors (for KV Builder.load_string context) ─────────
    @staticmethod
    def get_color(color_name: str) -> tuple:
        """Get a theme color by name."""
        color_map = {
            "primary": Colors.PRIMARY,
            "secondary": Colors.SECONDARY,
            "bg_base": Colors.BG_BASE,
            "bg_card": Colors.BG_CARD,
            "bg_input": Colors.BG_INPUT,
            "text_primary": Colors.TEXT_PRIMARY,
            "text_secondary": Colors.TEXT_SECONDARY,
            "text_hint": Colors.TEXT_HINT,
            "success": Colors.SUCCESS,
            "warning": Colors.WARNING,
            "error": Colors.ERROR,
            "info": Colors.INFO,
        }
        return color_map.get(color_name, Colors.TEXT_PRIMARY)


if __name__ == "__main__":
    FloraApp().run()
