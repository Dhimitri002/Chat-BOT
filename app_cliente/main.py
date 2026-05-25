"""
Flora Platform - App Cliente
Aplicativo KivyMD para clientes gerenciarem seus chatbots WhatsApp.
"""
import os
from pathlib import Path

from kivy.config import Config
Config.set("graphics", "width", "400")
Config.set("graphics", "height", "700")
Config.set("graphics", "minimum_width", "350")
Config.set("graphics", "minimum_height", "600")

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

# Tema escuro premium
from kivy.utils import get_color_from_hex


class ThemeColors:
    """Cores do tema premium escuro."""
    PRIMARY = "#1a1a2e"
    SECONDARY = "#16213e"
    ACCENT = "#0f3460"
    HIGHLIGHT = "#e94560"
    SUCCESS = "#4ecca3"
    WARNING = "#f9a825"
    ERROR = "#ef5350"
    SURFACE = "#16213e"
    CARD = "#1a1a2e"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    TEXT_HINT = "#757575"
    DIVIDER = "#2a2a4a"


class MainScreenManager(MDScreenManager):
    pass


class FloraClienteApp(MDApp):
    """Aplicativo principal do cliente Flora Platform."""

    # Propriedades reativas
    is_authenticated = BooleanProperty(False)
    current_user = ObjectProperty(None, allownone=True)
    user_name = StringProperty("")
    user_email = StringProperty("")
    user_plan = StringProperty("Gratuito")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Flora Platform"
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
        self.ws_url = os.getenv("WS_URL", "ws://localhost:8000")

    def build(self):
        """Constroi a aplicacao."""
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Red"

        # Configurar cores customizadas
        self.theme_cls.primary_hue = "700"
        self.theme_cls.accent_hue = "500"

        # Configurar janela
        Window.clearcolor = get_color_from_hex(ThemeColors.PRIMARY)

        # Carregar telas
        self._load_screens()

        return self.screen_manager

    def _load_screens(self):
        """Carrega todas as telas do app."""
        from app_cliente.screens.splash_screen import SplashScreen
        from app_cliente.screens.login_screen import LoginScreen
        from app_cliente.screens.register_screen import RegisterScreen
        from app_cliente.screens.onboarding_screen import OnboardingScreen
        from app_cliente.screens.home_screen import HomeScreen
        from app_cliente.screens.bot_create_screen import BotCreateScreen
        from app_cliente.screens.bot_panel_screen import BotPanelScreen
        from app_cliente.screens.chat_screen import ChatScreen
        from app_cliente.screens.commands_screen import CommandsScreen
        from app_cliente.screens.whatsapp_screen import WhatsAppScreen
        from app_cliente.screens.settings_screen import SettingsScreen
        from app_cliente.screens.flora_chat_screen import FloraChatScreen
        from app_cliente.screens.plans_screen import PlansScreen
        from app_cliente.screens.support_screen import SupportScreen

        self.screen_manager = MainScreenManager()

        # Adicionar telas
        screens = [
            SplashScreen(name="splash"),
            LoginScreen(name="login"),
            RegisterScreen(name="register"),
            OnboardingScreen(name="onboarding"),
            HomeScreen(name="home"),
            BotCreateScreen(name="bot_create"),
            BotPanelScreen(name="bot_panel"),
            ChatScreen(name="chat"),
            CommandsScreen(name="commands"),
            WhatsAppScreen(name="whatsapp"),
            SettingsScreen(name="settings"),
            FloraChatScreen(name="flora_chat"),
            PlansScreen(name="plans"),
            SupportScreen(name="support"),
        ]

        for screen in screens:
            self.screen_manager.add_widget(screen)

    def on_start(self):
        """Chamado quando o app inicia."""
        self._check_auth()

    def _check_auth(self):
        """Verifica se o usuario ja esta autenticado."""
        from app_cliente.services.auth import AuthService
        auth = AuthService()
        token = auth.get_token()
        if token:
            self.is_authenticated = True
            self.current_user = auth.get_user()
            if self.current_user:
                self.user_name = self.current_user.get("full_name", "")
                self.user_email = self.current_user.get("email", "")
                self.user_plan = self.current_user.get("plan", "Gratuito")
            self.screen_manager.current = "home"
        else:
            self.screen_manager.current = "login"

    def logout(self):
        """Faz logout do usuario."""
        from app_cliente.services.auth import AuthService
        auth = AuthService()
        auth.logout()
        self.is_authenticated = False
        self.current_user = None
        self.user_name = ""
        self.user_email = ""
        self.user_plan = "Gratuito"
        self.screen_manager.current = "login"

    def switch_screen(self, screen_name: str, direction: str = "left"):
        """Navega para outra tela."""
        self.screen_manager.transition.direction = direction
        self.screen_manager.current = screen_name

    def show_dialog(self, title: str, text: str):
        """Mostra dialogo de alerta."""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                    on_release=lambda x: dialog.dismiss(),
                ),
            ],
        )
        dialog.open()

    def show_snackbar(self, text: str):
        """Mostra snackbar de notificacao."""
        from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

        snackbar = MDSnackbar(
            MDSnackbarText(text=text),
            y=24,
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            md_bg_color=get_color_from_hex(ThemeColors.SURFACE),
        )
        snackbar.open()


if __name__ == "__main__":
    FloraClienteApp().run()
