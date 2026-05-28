# ═══════════════════════════════════════════════════════════════
# Flora Platform — Client App (KivyMD)
# ═══════════════════════════════════════════════════════════════
# Aplicativo do cliente final da plataforma Flora.
# Gerencie seu chatbot WhatsApp com elegância e simplicidade.
# ═══════════════════════════════════════════════════════════════

import os
import json
import threading
from pathlib import Path

from kivy.config import Config
Config.set("graphics", "width", "400")
Config.set("graphics", "height", "700")

from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager, FadeTransition

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.divider import MDDivider
from kivymd.uix.list import MDList, MDListItem, MDListItemHeadlineText, MDListItemSupportingText
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.relativelayout import RelativeLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFillRoundFlatButton, MDIconButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.navigationdrawer import MDNavigationDrawer, MDNavigationDrawerMenu, MDNavigationDrawerItem, MDNavigationDrawerLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.fitimage import FitImage
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.progressindicator import MDLinearProgressIndicator, MDCircularProgressIndicator
from kivymd.uix.swiper import MDSwiper, MDSwiperItem
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelHeader, MDExpansionPanelContent
from kivymd.uix.behaviors import HoverBehavior
from kivymd.uix.behaviors.magic_behavior import MagicBehavior
from kivymd.font_definitions import theme_font_styles
from kivymd.material_resources import DEVICE_TYPE

# ── Flora Color Palette ──────────────────────────────────────────
FLORA_PRIMARY = (0.424, 0.388, 1.0, 1)       # #6C63FF deep purple
FLORA_ACCENT = (1.0, 0.420, 0.616, 1)         # #FF6B9D soft pink
FLORA_BG = (0.102, 0.102, 0.180, 1)           # #1A1A2E dark blue
FLORA_SURFACE = (0.086, 0.129, 0.243, 1)      # #16213E
FLORA_SUCCESS = (0.298, 0.686, 0.314, 1)      # #4CAF50
FLORA_WARNING = (1.0, 0.600, 0.0, 1)          # #FF9800
FLORA_ERROR = (0.957, 0.263, 0.212, 1)        # #F44336
FLORA_TEXT_PRIMARY = (1.0, 1.0, 1.0, 1)       # White
FLORA_TEXT_SECONDARY = (0.7, 0.7, 0.75, 1)    # Light gray
FLORA_CARD_BG = (0.13, 0.16, 0.28, 1)         # Slightly lighter surface

# ── Token Storage ─────────────────────────────────────────────────
TOKEN_DIR = Path.home() / ".flora"
TOKEN_FILE = TOKEN_DIR / "client_token.json"


def save_token_data(data: dict):
    """Save token and user data to local storage."""
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_token_data() -> dict | None:
    """Load token data from local storage."""
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def clear_token_data():
    """Remove stored token data."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


def get_stored_token() -> str | None:
    """Get the stored access token."""
    data = load_token_data()
    if data:
        return data.get("access_token")
    return None


def get_stored_user() -> dict | None:
    """Get the stored user info."""
    data = load_token_data()
    if data:
        return data.get("user")
    return None


def get_stored_bot_id() -> str | None:
    """Get the stored bot ID."""
    data = load_token_data()
    if data:
        return data.get("bot_id")
    return None


# ── API Client ─────────────────────────────────────────────────────
API_BASE_URL = "http://localhost:8000/api/v1"


def api_request(method: str, endpoint: str, data: dict = None, token: str = None) -> dict:
    """
    Make an API request. Runs in a thread-safe way.
    Returns a dict with 'success', 'data', and 'error' keys.
    """
    import urllib.request
    import urllib.error

    url = f"{API_BASE_URL}{endpoint}"
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")

        body = None
        if data:
            body = json.dumps(data).encode("utf-8")
            req.data = body

        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = resp.read().decode("utf-8")
            return {"success": True, "data": json.loads(resp_body) if resp_body else {}, "error": None}
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            err_data = json.loads(err_body)
            return {"success": False, "data": None, "error": err_data.get("detail", str(e))}
        except Exception:
            return {"success": False, "data": None, "error": str(e)}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


def api_request_async(method: str, endpoint: str, data: dict = None, token: str = None,
                      callback=None):
    """Make an API request in a background thread, call callback with result."""

    def _do_request():
        result = api_request(method, endpoint, data, token)
        if callback:
            Clock.schedule_once(lambda dt: callback(result), 0)

    thread = threading.Thread(target=_do_request, daemon=True)
    thread.start()


# ── Import Screens ────────────────────────────────────────────────
from apps.client.screens.splash_screen import SplashScreen
from apps.client.screens.welcome_screen import WelcomeScreen
from apps.client.screens.license_screen import LicenseScreen
from apps.client.screens.onboarding_screen import OnboardingScreen
from apps.client.screens.dashboard_screen import DashboardScreen
from apps.client.screens.whatsapp_qr_screen import WhatsAppQrScreen
from apps.client.screens.chat_screen import ChatScreen
from apps.client.screens.bot_config_screen import BotConfigScreen
from apps.client.screens.intents_screen import IntentsScreen
from apps.client.screens.commands_screen import CommandsScreen
from apps.client.screens.plans_screen import PlansScreen
from apps.client.screens.flora_chat_screen import FloraChatScreen
from apps.client.screens.profile_screen import ProfileScreen
from apps.client.screens.settings_screen import SettingsScreen


class FloraClientApp(MDApp):
    """Flora Platform — Client Application."""

    # Properties
    current_user = StringProperty("")
    current_bot_id = StringProperty("")
    is_authenticated = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Flora Platform"
        self._token = None
        self._user = None

    def build(self):
        """Build the application."""
        self.theme_cls.primary_palette = "Purple"
        self.theme_cls.accent_palette = "Pink"
        self.theme_cls.theme_style = "Dark"

        # Set custom colors
        self.theme_cls.primaryColor = FLORA_PRIMARY
        self.theme_cls.backgroundColor = FLORA_BG

        # Create screen manager with fade transition
        self.sm = ScreenManager(transition=FadeTransition(duration=0.3))

        # Add all screens
        self.sm.add_widget(SplashScreen(name="splash"))
        self.sm.add_widget(WelcomeScreen(name="welcome"))
        self.sm.add_widget(LicenseScreen(name="license"))
        self.sm.add_widget(OnboardingScreen(name="onboarding"))
        self.sm.add_widget(DashboardScreen(name="dashboard"))
        self.sm.add_widget(WhatsAppQrScreen(name="whatsapp_qr"))
        self.sm.add_widget(ChatScreen(name="chat"))
        self.sm.add_widget(BotConfigScreen(name="bot_config"))
        self.sm.add_widget(IntentsScreen(name="intents"))
        self.sm.add_widget(CommandsScreen(name="commands"))
        self.sm.add_widget(PlansScreen(name="plans"))
        self.sm.add_widget(FloraChatScreen(name="flora_chat"))
        self.sm.add_widget(ProfileScreen(name="profile"))
        self.sm.add_widget(SettingsScreen(name="settings"))

        return self.sm

    def on_start(self):
        """Called when the app starts."""
        Clock.schedule_once(self._check_auth, 0.5)

    def _check_auth(self, dt):
        """Check if user is already authenticated."""
        token = get_stored_token()
        user = get_stored_user()
        bot_id = get_stored_bot_id()

        if token and user:
            self._token = token
            self._user = user
            self.is_authenticated = True
            self.current_user = user.get("name", "Usuária")
            self.current_bot_id = bot_id or ""
            self.sm.current = "dashboard"
        else:
            self.sm.current = "welcome"

    def get_token(self) -> str | None:
        """Get the current auth token."""
        return self._token

    def get_user(self) -> dict | None:
        """Get the current user info."""
        return self._user

    def set_auth(self, token: str, user: dict, bot_id: str = None):
        """Set authentication data."""
        self._token = token
        self._user = user
        self.is_authenticated = True
        self.current_user = user.get("name", "Usuária")
        if bot_id:
            self.current_bot_id = bot_id
        save_token_data({
            "access_token": token,
            "user": user,
            "bot_id": bot_id or "",
        })

    def logout(self):
        """Logout the current user."""
        self._token = None
        self._user = None
        self.is_authenticated = False
        self.current_user = ""
        self.current_bot_id = ""
        clear_token_data()
        self.sm.current = "welcome"

    def show_snackbar(self, text: str, bg_color=None):
        """Show a snackbar notification."""
        if bg_color is None:
            bg_color = FLORA_PRIMARY
        snackbar = MDSnackbar(
            MDSnackbarText(text=text),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            background_color=bg_color,
        )
        snackbar.open()

    def show_error_dialog(self, title: str, message: str):
        """Show an error dialog."""
        self.dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=message),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="OK"),
                    style="text",
                    on_release=lambda x: self.dialog.dismiss(),
                ),
                spacing=dp(8),
            ),
        )
        self.dialog.open()

    def switch_screen(self, screen_name: str):
        """Switch to a different screen with animation."""
        self.sm.current = screen_name


if __name__ == "__main__":
    FloraClientApp().run()
