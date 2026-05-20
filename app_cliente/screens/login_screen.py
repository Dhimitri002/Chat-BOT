"""Login Screen - Tela de login."""
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard


class LoginScreen(MDScreen):
    """Tela de login do cliente."""

    def on_enter(self):
        self.build_ui()

    def build_ui(self):
        from app_cliente.main import ThemeColors

        layout = MDBoxLayout(
            orientation="vertical",
            spacing=16,
            padding=32,
            md_bg_color=get_color_from_hex(ThemeColors.PRIMARY),
        )

        layout.add_widget(MDBoxLayout(size_hint_y=0.15))

        # Título
        layout.add_widget(
            MDLabel(
                text="🌸 Bem-vindo de volta",
                font_style="H4",
                halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            )
        )
        layout.add_widget(
            MDLabel(
                text="Entre na sua conta Flora",
                font_style="Body2",
                halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
            )
        )

        layout.add_widget(MDBoxLayout(size_hint_y=0.05))

        # Card de login
        card = MDCard(
            orientation="vertical",
            spacing=16,
            padding=24,
            size_hint=(1, None),
            height=320,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            radius=[16],
            elevation=4,
        )

        # Email
        self.email_field = MDTextField(
            hint_text="Email",
            icon_right="email",
            mode="round",
            size_hint_x=1,
        )
        card.add_widget(self.email_field)

        # Senha
        self.password_field = MDTextField(
            hint_text="Senha",
            icon_right="lock",
            mode="round",
            password=True,
            size_hint_x=1,
        )
        card.add_widget(self.password_field)

        # Botão login
        login_btn = MDRaisedButton(
            text="ENTRAR",
            size_hint=(1, None),
            height=48,
            md_bg_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            on_release=self._do_login,
        )
        card.add_widget(login_btn)

        # Link registro
        register_btn = MDFlatButton(
            text="Não tem conta? Cadastre-se",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            pos_hint={"center_x": 0.5},
            on_release=lambda x: setattr(self.manager, "current", "register"),
        )
        card.add_widget(register_btn)

        layout.add_widget(card)
        layout.add_widget(MDBoxLayout())  # Spacer

        self.clear_widgets()
        self.add_widget(layout)

    def _do_login(self, *args):
        """Realiza login."""
        email = self.email_field.text.strip()
        password = self.password_field.text.strip()

        if not email or not password:
            self._show_error("Preencha todos os campos.")
            return

        # Fazer login via API
        from app_cliente.services.api_client import APIClient
        from app_cliente.services.auth import AuthService

        api = APIClient()
        result = api.login(email, password)

        if result.get("success"):
            auth = AuthService()
            auth.save_token(result["token"])
            auth.save_user(result.get("user", {}))
            self.manager.current = "home"
        else:
            self._show_error(result.get("error", "Erro ao fazer login."))

    def _show_error(self, message):
        """Mostra erro."""
        from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
        from app_cliente.main import ThemeColors

        MDSnackbar(
            MDSnackbarText(text=message),
            y=24,
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            md_bg_color=get_color_from_hex(ThemeColors.ERROR),
        ).open()
