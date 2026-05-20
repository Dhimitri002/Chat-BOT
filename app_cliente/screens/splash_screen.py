"""Splash Screen - Tela de abertura."""
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.boxlayout import MDBoxLayout


class SplashScreen(MDScreen):
    """Tela de abertura com logo e loading."""

    def on_enter(self):
        """Chamado ao entrar na tela."""
        self.build_ui()
        # Navegar após 2.5 segundos
        Clock.schedule_once(self._go_to_next, 2.5)

    def build_ui(self):
        """Constrói a interface."""
        from app_cliente.main import ThemeColors

        layout = MDBoxLayout(
            orientation="vertical",
            spacing=20,
            padding=40,
            md_bg_color=get_color_from_hex(ThemeColors.PRIMARY),
        )

        layout.add_widget(MDBoxLayout())  # Spacer

        # Logo / Título
        layout.add_widget(
            MDLabel(
                text="🌸 Flora",
                font_style="H2",
                halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            )
        )

        layout.add_widget(
            MDLabel(
                text="Plataforma de Chatbots Inteligentes",
                font_style="Body1",
                halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
            )
        )

        layout.add_widget(MDBoxLayout())  # Spinner area

        # Loading spinner
        spinner = MDSpinner(
            size_hint=(None, None),
            size=(46, 46),
            pos_hint={"center_x": 0.5},
            active=True,
        )
        layout.add_widget(spinner)

        layout.add_widget(
            MDLabel(
                text="Carregando...",
                font_style="Caption",
                halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
            )
        )

        layout.add_widget(MDBoxLayout())  # Spacer

        self.clear_widgets()
        self.add_widget(layout)

    def _go_to_next(self, dt):
        """Navega para a próxima tela."""
        # Verificar auth
        from app_cliente.services.auth import AuthService
        auth = AuthService()
        if auth.get_token():
            self.manager.current = "home"
        else:
            self.manager.current = "login"
