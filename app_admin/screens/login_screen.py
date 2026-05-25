"""
LoginScreen — Admin authentication screen.

Features:
  - Email & password fields
  - Dark premium card centred on background
  - Loading state + error feedback
  - Keyboard shortcut (Enter) to submit
"""

from kivy.animation import Animation
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.spinner import MDSpinner

from app_admin.styles.theme import Colors, Theme


class LoginScreen(MDScreen):
    """Email + password login for administrators."""

    error_message = StringProperty("")
    loading = BooleanProperty(False)

    def __init__(self, app: "FloraAdminApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._build()

    # ── build UI ────────────────────────────────────────────────────────
    def _build(self):
        # Root layout — centre the card
        root = MDBoxLayout(
            orientation="vertical",
            md_bg_color=Colors.BG_BASE,
        )

        spacer_top = MDBoxLayout(size_hint_y=0.2)
        root.add_widget(spacer_top)

        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=0.6,
            padding=[Theme.SPACE_2XL, 0],
        )

        # Spacer left
        row.add_widget(MDBoxLayout(size_hint_x=0.3))

        # Login card
        self._card = MDCard(
            orientation="vertical",
            padding=Theme.SPACE_2XL,
            spacing=Theme.SPACE_MD,
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_XL],
            elevation=Theme.ELEVATION_MODAL,
            size_hint=(0.4, None),
            height=dp(420),
            pos_hint={"center_y": 0.5},
        )

        # Logo / icon area
        icon_box = MDBoxLayout(
            size_hint_y=None,
            height=dp(64),
            padding=[0, Theme.SPACE_SM],
        )
        logo_icon = MDIconButton(
            icon="flower",
            theme_text_color="Custom",
            text_color=Colors.PRIMARY,
            font_size=dp(48),
            size_hint=(None, None),
            size=(dp(64), dp(64)),
            pos_hint={"center_x": 0.5},
        )
        icon_box.add_widget(logo_icon)
        self._card.add_widget(icon_box)

        # Title
        title = MDLabel(
            text="Flora Admin",
            font_style="H4",
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(40),
        )
        self._card.add_widget(title)

        subtitle = MDLabel(
            text="Painel Administrativo",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(20),
        )
        self._card.add_widget(subtitle)

        # Spacer
        self._card.add_widget(MDBoxLayout(size_hint_y=None, height=dp(16)))

        # Email field
        self._email_field = MDTextField(
            hint_text="Email",
            mode="round",
            icon_left="email",
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            radius=[Theme.RADIUS_MEDIUM],
        )
        self._card.add_widget(self._email_field)

        # Password field
        self._password_field = MDTextField(
            hint_text="Senha",
            mode="round",
            icon_left="lock",
            password=True,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            radius=[Theme.RADIUS_MEDIUM],
        )
        self._password_field.bind(on_text_validate=self._on_submit)
        self._card.add_widget(self._password_field)

        # Error label
        self._error_label = MDLabel(
            text="",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.ERROR,
            size_hint_y=None,
            height=dp(20),
        )
        self._card.add_widget(self._error_label)
        self.bind(error_message=lambda *a: setattr(self._error_label, "text", self.error_message))

        # Login button
        self._login_btn = MDRaisedButton(
            text="Entrar",
            size_hint_y=None,
            height=dp(48),
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.BG_BASE,
            font_size=dp(16),
            radius=[Theme.RADIUS_MEDIUM],
            on_release=self._on_submit,
        )
        self._card.add_widget(self._login_btn)

        # Loading spinner (hidden by default)
        self._spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={"center_x": 0.5},
            active=False,
        )
        self._card.add_widget(self._spinner)

        row.add_widget(self._card)
        row.add_widget(MDBoxLayout(size_hint_x=0.3))

        root.add_widget(row)
        root.add_widget(MDBoxLayout(size_hint_y=0.2))

        self.add_widget(root)

        # Bind loading state
        self.bind(loading=self._on_loading_changed)

    # ── event handlers ───────────────────────────────────────────────────
    def _on_loading_changed(self, *args):
        self._login_btn.disabled = self.loading
        self._login_btn.opacity = 0.4 if self.loading else 1
        self._spinner.active = self.loading

    def _on_submit(self, *args):
        email = (self._email_field.text or "").strip()
        password = (self._password_field.text or "").strip()

        if not email:
            self.error_message = "Informe seu email."
            return
        if not password:
            self.error_message = "Informe sua senha."
            return

        self.error_message = ""
        self.loading = True

        def _do_login():
            try:
                success = self._app.login(email, password)
                if success:
                    self._app.on_login_success()
                else:
                    self.error_message = "Credenciais inválidas."
            except Exception as e:
                self.error_message = f"Erro de conexão: {e}"
            finally:
                self.loading = False

        import threading
        threading.Thread(target=_do_login, daemon=True).start()
