"""
Login Screen for the Flora Admin Panel.
Admin authentication with email and password.
"""
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.relativelayout import RelativeLayout

from app_admin.services.auth import auth_service
from app_admin.utils.constants import Colors
from app_admin.utils.helpers import validate_email


class LoginScreen(MDScreen):
    """Admin login screen with dark premium UI."""

    error_text = StringProperty("")
    loading = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "login"
        self._build_ui()

    def _build_ui(self):
        """Build the login screen UI."""
        # Main layout
        main_layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(40),
            spacing=dp(16),
            md_bg_color=Colors.BG_DARK,
        )

        # Center container
        center_box = MDBoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(400),
            height=dp(500),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            spacing=dp(20),
        )

        # Spacer
        main_layout.add_widget(MDBoxLayout(size_hint_y=0.15))

        # Logo / Branding area
        branding_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(120),
            spacing=dp(8),
        )

        # Logo icon
        logo_btn = MDIconButton(
            icon="robot",
            icon_size=dp(64),
            theme_icon_color="Custom",
            icon_color=Colors.PRIMARY_LIGHT,
            pos_hint={"center_x": 0.5},
        )
        branding_box.add_widget(logo_btn)

        # App title
        title_label = MDLabel(
            text="Flora Admin",
            halign="center",
            font_style="H4",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            bold=True,
        )
        branding_box.add_widget(title_label)

        # Subtitle
        subtitle_label = MDLabel(
            text="Painel Administrativo",
            halign="center",
            font_style="Subtitle1",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
        )
        branding_box.add_widget(subtitle_label)

        center_box.add_widget(branding_box)

        # Spacer
        center_box.add_widget(MDBoxLayout(size_hint_y=None, height=dp(20)))

        # Login card
        login_card = MDCard(
            orientation="vertical",
            padding=dp(24),
            spacing=dp(16),
            md_bg_color=Colors.BG_CARD,
            radius=[dp(16)],
            elevation=dp(8),
        )

        # Email field
        self.email_field = MDTextField(
            hint_text="Email",
            mode="round",
            icon_left="account",
            text="",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            icon_color_normal=Colors.TEXT_SECONDARY,
            icon_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(12)],
        )
        login_card.add_widget(self.email_field)

        # Password field
        self.password_field = MDTextField(
            hint_text="Senha",
            mode="round",
            icon_left="lock",
            password=True,
            text="",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            icon_color_normal=Colors.TEXT_SECONDARY,
            icon_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(12)],
        )
        login_card.add_widget(self.password_field)

        # Error label
        self.error_label = MDLabel(
            text="",
            halign="center",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.ERROR,
            size_hint_y=None,
            height=dp(20),
        )
        login_card.add_widget(self.error_label)

        # Login button
        self.login_button = MDRaisedButton(
            text="ENTRAR",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.TEXT_PRIMARY,
            font_size=dp(16),
            radius=[dp(12)],
            on_release=self._on_login,
        )
        login_card.add_widget(self.login_button)

        # Loading spinner (hidden by default)
        self.spinner_box = MDBoxLayout(
            size_hint_y=None,
            height=dp(0),
        )
        self.spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            active=False,
            color=Colors.PRIMARY_LIGHT,
        )
        self.spinner_box.add_widget(self.spinner)
        login_card.add_widget(self.spinner_box)

        center_box.add_widget(login_card)

        # Bottom spacer
        main_layout.add_widget(center_box)
        main_layout.add_widget(MDBoxLayout(size_hint_y=0.15))

        # Version label
        version_label = MDLabel(
            text="Flora Platform v1.0.0",
            halign="center",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_y=None,
            height=dp(20),
        )
        main_layout.add_widget(version_label)

        self.add_widget(main_layout)

    def _on_login(self, *args):
        """Handle login button press."""
        email = self.email_field.text.strip()
        password = self.password_field.text.strip()

        # Validation
        if not email:
            self.error_label.text = "Digite seu email"
            return
        if not validate_email(email):
            self.error_label.text = "Email invalido"
            return
        if not password:
            self.error_label.text = "Digite sua senha"
            return

        self.error_label.text = ""
        self.loading = True
        self.login_button.disabled = True
        self.login_button.text = "ENTRANDO..."
        self.spinner_box.height = dp(40)
        self.spinner.active = True

        # Perform login
        def _do_login(dt):
            try:
                success, message = auth_service.login(email, password)
                self.loading = False
                self.login_button.disabled = False
                self.login_button.text = "ENTRAR"
                self.spinner_box.height = dp(0)
                self.spinner.active = False

                if success:
                    self.error_label.text = ""
                    self.manager.current = "dashboard"
                else:
                    self.error_label.text = message
            except Exception as e:
                self.loading = False
                self.login_button.disabled = False
                self.login_button.text = "ENTRAR"
                self.spinner_box.height = dp(0)
                self.spinner.active = False
                self.error_label.text = f"Erro: {str(e)}"

        Clock.schedule_once(_do_login, 0.1)

    def on_pre_enter(self):
        """Called when screen is about to be entered."""
        self.email_field.text = ""
        self.password_field.text = ""
        self.error_label.text = ""
        self.loading = False
        self.login_button.disabled = False
        self.login_button.text = "ENTRAR"
