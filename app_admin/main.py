"""
Flora Platform — Admin Panel
Aplicativo KivyMD para administração da plataforma.
"""
import os
import sys

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kivy.config import Config
Config.set("graphics", "width", "1200")
Config.set("graphics", "height", "800")
Config.set("graphics", "minimum_width", "900")
Config.set("graphics", "minimum_height", "600")

from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen

# Import screens
from app_admin.screens.login_screen import LoginScreen
from app_admin.screens.dashboard_screen import DashboardScreen
from app_admin.screens.bots_screen import BotsScreen
from app_admin.screens.licenses_screen import LicensesScreen
from app_admin.screens.users_screen import UsersScreen
from app_admin.screens.plans_screen import PlansScreen
from app_admin.screens.analytics_screen import AnalyticsScreen

from app_admin.utils.constants import Colors


class ThemeColors:
    """Cores do tema do app admin."""
    PRIMARY = Colors.PRIMARY
    SECONDARY = Colors.SECONDARY
    ACCENT = Colors.ACCENT
    BG_DARK = Colors.BG_DARK
    BG_CARD = Colors.BG_CARD
    BG_SIDEBAR = Colors.BG_SIDEBAR
    TEXT_PRIMARY = Colors.TEXT_PRIMARY
    TEXT_SECONDARY = Colors.TEXT_SECONDARY
    SUCCESS = Colors.SUCCESS
    WARNING = Colors.WARNING
    ERROR = Colors.ERROR
    INFO = Colors.INFO


class Sidebar(MDScreen):
    """Sidebar de navegação do admin panel."""
    pass


class MainScreen(MDScreen):
    """Tela principal com sidebar e conteúdo."""
    pass


class AdminApp(MDApp):
    """Aplicação principal do Admin Panel."""

    # Propriedades reativas
    is_authenticated = BooleanProperty(False)
    current_user_name = StringProperty("")
    current_user_email = StringProperty("")
    current_user_role = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Flora Platform — Admin"
        self.theme_cls.primary_palette = "Purple"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Dark"

    def build(self):
        """Constrói a aplicação."""
        self.theme_cls.primary_hue = "500"
        self.theme_cls.accent_hue = "500"

        # Criar screen manager
        sm = MDScreenManager()

        # Adicionar telas
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(BotsScreen(name="bots"))
        sm.add_widget(LicensesScreen(name="licenses"))
        sm.add_widget(UsersScreen(name="users"))
        sm.add_widget(PlansScreen(name="plans"))
        sm.add_widget(AnalyticsScreen(name="analytics"))

        return sm

    def on_start(self):
        """Chamado quando o app inicia."""
        # Verificar se já está logado
        from app_admin.services.auth import AuthService
        if AuthService.is_logged_in():
            self.is_authenticated = True
            user = AuthService.get_current_user()
            if user:
                self.current_user_name = user.get("full_name", "")
                self.current_user_email = user.get("email", "")
                self.current_user_role = user.get("role", "")
            self.root.current = "dashboard"
        else:
            self.root.current = "login"

    def logout(self):
        """Faz logout do admin."""
        from app_admin.services.auth import AuthService
        AuthService.logout()
        self.is_authenticated = False
        self.current_user_name = ""
        self.current_user_email = ""
        self.current_user_role = ""
        self.root.current = "login"

    def switch_screen(self, screen_name: str):
        """Troca para a tela especificada."""
        if self.root:
            self.root.current = screen_name


if __name__ == "__main__":
    AdminApp().run()
