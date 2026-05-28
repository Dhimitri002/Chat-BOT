# ═══════════════════════════════════════════════════════════════
# Flora Platform — Tela de Login
# ═══════════════════════════════════════════════════════════════

from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, SlideTransition

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField, MDTextFieldRect
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.dialog import MDDialog
from kivymd.toast import toast

from apps.shared.api_client import api


class LoginScreen(Screen):
    """Tela de login do painel administrativo."""

    loading = BooleanProperty(False)
    error_message = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "login"
        self._dialog = None
        self._build()

    def _build(self):
        """Constrói a tela de login."""
        # Background
        self.md_bg_color = (0.059, 0.063, 0.137, 1)  # BG_DARK

        # Layout centralizado
        root = MDBoxLayout(
            orientation="vertical",
            padding=dp(32),
            spacing=dp(0),
        )

        # Espaçador superior
        top_spacer = MDBoxLayout(size_hint_y=0.2)
        root.add_widget(top_spacer)

        # Card de login
        login_card = MDCard(
            orientation="vertical",
            size_hint=(None, None),
            size=(dp(400), dp(480)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            radius=[dp(24)],
            elevation=4,
            padding=dp(32),
            spacing=dp(16),
            md_bg_color=(0.11, 0.165, 0.298, 1),  # BG_CARD
        )

        # Logo / Título
        logo_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(80),
            spacing=dp(4),
        )

        logo_title = MDLabel(
            text="🌸 Flora Platform",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),  # PRIMARY
            font_style="H4",
            bold=True,
            halign="center",
            size_hint_y=None,
            height=dp(40),
        )

        logo_subtitle = MDLabel(
            text="Painel Administrativo",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),  # TEXT_SECONDARY
            font_style="Body2",
            halign="center",
            size_hint_y=None,
            height=dp(24),
        )

        logo_box.add_widget(logo_title)
        logo_box.add_widget(logo_subtitle)
        login_card.add_widget(logo_box)

        # Espaço
        login_card.add_widget(MDBoxLayout(size_hint_y=None, height=dp(8)))

        # Campo de Email
        self.email_field = MDTextField(
            hint_text="Email",
            icon_right="account",
            mode="round",
            radius=[dp(10)],
            hint_text_color_normal=(0.376, 0.49, 0.545, 1),
            text_color_normal=(1, 1, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            icon_color_normal=(0.376, 0.49, 0.545, 1),
            icon_color_focus=(0.424, 0.388, 1.0, 1),
            line_color_normal=(0.227, 0.294, 0.431, 1),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            fill_color_normal=(0.055, 0.106, 0.243, 1),  # BG_INPUT
            size_hint_y=None,
            height=dp(52),
        )
        login_card.add_widget(self.email_field)

        # Campo de Senha
        self.password_field = MDTextField(
            hint_text="Senha",
            icon_right="eye-off",
            mode="round",
            radius=[dp(10)],
            password=True,
            hint_text_color_normal=(0.376, 0.49, 0.545, 1),
            text_color_normal=(1, 1, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            icon_color_normal=(0.376, 0.49, 0.545, 1),
            icon_color_focus=(0.424, 0.388, 1.0, 1),
            line_color_normal=(0.227, 0.294, 0.431, 1),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            fill_color_normal=(0.055, 0.106, 0.243, 1),  # BG_INPUT
            size_hint_y=None,
            height=dp(52),
        )
        self.password_field.bind(icon_right=self._toggle_password)
        self.password_field.bind(focus=self._on_password_focus)
        login_card.add_widget(self.password_field)

        # Mensagem de erro
        self.error_label = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color=(0.957, 0.263, 0.212, 1),  # ERROR
            font_style="Caption",
            halign="center",
            size_hint_y=None,
            height=dp(20),
            opacity=0,
        )
        login_card.add_widget(self.error_label)

        # Espaço
        login_card.add_widget(MDBoxLayout(size_hint_y=None, height=dp(4)))

        # Botão de Login
        self.login_btn = MDRaisedButton(
            text="Entrar",
            size_hint=(1, None),
            height=dp(48),
            radius=[dp(12)],
            md_bg_color=(0.424, 0.388, 1.0, 1),  # PRIMARY
            text_color=(1, 1, 1, 1),
            font_size=dp(16),
            bold=True,
            pos_hint={"center_x": 0.5},
        )
        self.login_btn.bind(on_release=self._do_login)
        login_card.add_widget(self.login_btn)

        # Loading spinner
        self.spinner_box = MDBoxLayout(
            size_hint_y=None,
            height=dp(0),
            opacity=0,
        )
        self.spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={"center_x": 0.5},
            active=False,
        )
        self.spinner_box.add_widget(self.spinner)
        login_card.add_widget(self.spinner_box)

        root.add_widget(login_card)

        # Espaçador inferior
        bottom_spacer = MDBoxLayout(size_hint_y=0.3)
        root.add_widget(bottom_spacer)

        self.add_widget(root)

    def _toggle_password(self, instance, value):
        """Alterna visibilidade da senha."""
        if value == "eye":
            instance.icon_right = "eye-off"
            instance.password = True
        else:
            instance.icon_right = "eye"
            instance.password = False

    def _on_password_focus(self, instance, focused):
        """Atualiza cor do ícone ao focar."""
        pass

    def _do_login(self, *args):
        """Executa o login."""
        email = self.email_field.text.strip()
        password = self.password_field.text

        # Validação
        if not email:
            self._show_error("Por favor, insira seu email.")
            return
        if not password:
            self._show_error("Por favor, insira sua senha.")
            return

        # Mostra loading
        self.loading = True
        self._show_loading(True)

        # Faz login em thread
        api.post_async("/auth/login", self._on_login_result, {
            "email": email,
            "password": password,
        })

    def _on_login_result(self, result):
        """Callback do resultado do login."""
        Clock.schedule_once(lambda dt: self._handle_login_result(result), 0)

    def _handle_login_result(self, result):
        """Processa o resultado do login (na thread principal)."""
        self.loading = False
        self._show_loading(False)

        if result.get("error"):
            msg = result.get("message", "Erro ao fazer login.")
            if result.get("unauthorized"):
                msg = "Email ou senha inválidos."
            self._show_error(msg)
            return

        # Salva token
        access_token = result.get("access_token")
        if not access_token:
            self._show_error("Resposta inválida do servidor.")
            return

        api.token = access_token

        # Limpa campos
        self.email_field.text = ""
        self.password_field.text = ""
        self._show_error("")

        # Navega para o dashboard
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "dashboard"

    def _show_error(self, message):
        """Exibe mensagem de erro."""
        self.error_message = message
        self.error_label.text = message
        self.error_label.opacity = 1 if message else 0

    def _show_loading(self, show):
        """Exibe/esconde o loading."""
        if show:
            self.login_btn.opacity = 0
            self.login_btn.disabled = True
            self.spinner_box.height = dp(48)
            self.spinner_box.opacity = 1
            self.spinner.active = True
        else:
            self.login_btn.opacity = 1
            self.login_btn.disabled = False
            self.spinner_box.height = dp(0)
            self.spinner_box.opacity = 0
            self.spinner.active = False

    def on_leave(self, *args):
        """Limpa campos ao sair da tela."""
        self._show_error("")
        self._show_loading(False)
        return super().on_leave(*args)
