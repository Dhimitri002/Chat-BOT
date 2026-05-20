"""Register Screen - Tela de cadastro."""
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard


class RegisterScreen(MDScreen):
    """Tela de cadastro de novo cliente."""

    def on_enter(self):
        self.build_ui()

    def build_ui(self):
        from app_cliente.main import ThemeColors

        layout = MDBoxLayout(
            orientation="vertical",
            spacing=12,
            padding=32,
            md_bg_color=get_color_from_hex(ThemeColors.PRIMARY),
        )

        layout.add_widget(MDBoxLayout(size_hint_y=0.08))

        layout.add_widget(
            MDLabel(
                text="🌸 Criar Conta",
                font_style="H4",
                halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            )
        )
        layout.add_widget(
            MDLabel(
                text="Comece a criar chatbots incríveis",
                font_style="Body2",
                halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
            )
        )

        layout.add_widget(MDBoxLayout(size_hint_y=0.04))

        card = MDCard(
            orientation="vertical",
            spacing=12,
            padding=24,
            size_hint=(1, None),
            height=400,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            radius=[16],
            elevation=4,
        )

        self.name_field = MDTextField(hint_text="Nome completo", icon_right="account", mode="round")
        card.add_widget(self.name_field)

        self.email_field = MDTextField(hint_text="Email", icon_right="email", mode="round")
        card.add_widget(self.email_field)

        self.password_field = MDTextField(hint_text="Senha", icon_right="lock", mode="round", password=True)
        card.add_widget(self.password_field)

        self.confirm_field = MDTextField(hint_text="Confirmar senha", icon_right="lock-check", mode="round", password=True)
        card.add_widget(self.confirm_field)

        card.add_widget(
            MDRaisedButton(
                text="CADASTRAR",
                size_hint=(1, None),
                height=48,
                md_bg_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                on_release=self._do_register,
            )
        )

        card.add_widget(
            MDFlatButton(
                text="Já tem conta? Entrar",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                pos_hint={"center_x": 0.5},
                on_release=lambda x: setattr(self.manager, "current", "login"),
            )
        )

        layout.add_widget(card)
        layout.add_widget(MDBoxLayout())

        self.clear_widgets()
        self.add_widget(layout)

    def _do_register(self, *args):
        name = self.name_field.text.strip()
        email = self.email_field.text.strip()
        password = self.password_field.text.strip()
        confirm = self.confirm_field.text.strip()

        if not all([name, email, password, confirm]):
            self._show_error("Preencha todos os campos.")
            return

        if password != confirm:
            self._show_error("As senhas não coincidem.")
            return

        if len(password) < 6:
            self._show_error("A senha deve ter pelo menos 6 caracteres.")
            return

        from app_cliente.services.api_client import APIClient
        api = APIClient()
        result = api.register(name, email, password)

        if result.get("success"):
            from app_cliente.services.auth import AuthService
            auth = AuthService()
            auth.save_token(result.get("token", ""))
            auth.save_user(result.get("user", {}))
            self.manager.current = "onboarding"
        else:
            self._show_error(result.get("error", "Erro ao cadastrar."))

    def _show_error(self, message):
        from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
        from app_cliente.main import ThemeColors
        MDSnackbar(
            MDSnackbarText(text=message), y=24,
            pos_hint={"center_x": 0.5}, size_hint_x=0.9,
            md_bg_color=get_color_from_hex(ThemeColors.ERROR),
        ).open()
