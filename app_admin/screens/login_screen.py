"""
LoginScreen — Premium admin login with dark theme.
"""

from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.spinner import MDSpinner

from app_admin.styles.theme import Colors, Theme


class LoginScreen(MDScreen):
    """Premium dark login screen for admin panel."""

    def __init__(self, app: "FloraAdminApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._is_loading = False
        self.build()

    def build(self):
        # Root
        root = MDBoxLayout(
            md_bg_color=Colors.BG_BASE,
        )
        self.add_widget(root)

        # Center the login card
        center = MDBoxLayout(
            orientation="vertical",
            padding=Theme.SPACE_XL,
            spacing=0,
            size_hint=(None, None),
            width=dp(420),
            height=dp(520),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        root.add_widget(MDBoxLayout())  # Top spacer
        root.add_widget(center)

        # Left spacer + card + right spacer
        h_center = MDBoxLayout(
            orientation="horizontal",
            spacing=0,
        )
        h_center.add_widget(MDBoxLayout())  # left spacer

        # Login card
        self._card = MDCard(
            orientation="vertical",
            padding=Theme.SPACE_XL,
            spacing=Theme.SPACE_MD,
            md_bg_color=Colors.BG_CARD,
            radius=dp(20),
            elevation=Theme.ELEVATION_HIGH,
            size_hint_y=None,
            height=dp(460),
        )

        # Logo area
        logo_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(100),
            padding=[0, dp(8), 0, 0],
        )
        logo_icon = MDIconButton(
            icon="robot",
            theme_text_color="Custom",
            text_color=Colors.PRIMARY,
            user_font_size=dp(56),
            pos_hint={"center_x": 0.5},
            size_hint_y=None,
            height=dp(72),
        )
        logo_box.add_widget(logo_icon)
        logo_box.add_widget(MDLabel(
            text="Flora Admin",
            font_style=Theme.H4,
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(32),
        ))
        self._card.add_widget(logo_box)

        # Subtitle
        self._card.add_widget(MDLabel(
            text="Painel Administrativo",
            font_style=Theme.CAPTION_STYLE,
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_y=None,
            height=dp(20),
        ))

        # Spacer
        self._card.add_widget(MDBoxLayout(size_hint_y=None, height=dp(8)))

        # Email field
        self._email_field = MDTextField(
            hint_text="Email",
            mode="round",
            text="admin@flora.bot",
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            icon_right="email",
            icon_right_color=Colors.TEXT_HINT,
            radius=dp(12),
        )
        self._card.add_widget(self._email_field)

        # Password field
        self._password_field = MDTextField(
            hint_text="Senha",
            mode="round",
            password=True,
            text="admin123",
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            icon_right="lock",
            icon_right_color=Colors.TEXT_HINT,
            radius=dp(12),
        )
        self._card.add_widget(self._password_field)

        # Error label
        self._error_label = MDLabel(
            text="",
            font_style=Theme.CAPTION_STYLE,
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.ERROR,
            size_hint_y=None,
            height=dp(0),
        )
        self._card.add_widget(self._error_label)

        # Spacer
        self._card.add_widget(MDBoxLayout(size_hint_y=None, height=dp(4)))

        # Login button
        self._login_btn = MDRaisedButton(
            text="ENTRAR",
            size_hint_y=None,
            height=dp(48),
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.TEXT_ON_ACCENT,
            theme_text_color="Custom",
            font_size=Theme.BOLD,
            bold=True,
            elevation=Theme.ELEVATION_LOW,
            radius=dp(12),
            on_release=self._on_login,
        )
        self._card.add_widget(self._login_btn)

        # Spinner (hidden)
        self._spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={"center_x": 0.5},
            color=Colors.PRIMARY,
            active=False,
        )
        self._card.add_widget(self._spinner)

        h_center.add_widget(self._card)
        h_center.add_widget(MDBoxLayout())  # right spacer
        center.add_widget(h_center)
        center.add_widget(MDBoxLayout())  # bottom spacer

        self._card.opacity = 0
        self._card.y -= dp(20)
        Clock.schedule_once(self._animate_in, 0.1)

    def _animate_in(self, dt):
        Animation(opacity=1, d=0.4, t="out_cubic").start(self._card)
        Animation(y=0, d=0.4, t="out_cubic").start(self._card)

    def _on_login(self, *args):
        if self._is_loading:
            return

        email = self._email_field.text.strip()
        password = self._password_field.text.strip()

        if not email or not password:
            self._show_error("Preencha todos os campos")
            return

        self._is_loading = True
        self._error_label.text = ""
        self._error_label.height = dp(0)
        self._login_btn.text = "ENTRANDO..."
        self._spinner.active = True

        # Simulate API call
        Clock.schedule_once(lambda dt: self._handle_login(email, password), 1.5)

    def _handle_login(self, email, password):
        # Successful login
        self._app.set_auth_token("mock-jwt-token-for-admin")
        self._app.set_current_user({
            "id": 1,
            "email": email,
            "name": "Admin Flora",
            "role": "admin",
        })
        self._app.switch_screen("dashboard")

    def _show_error(self, message):
        self._error_label.text = message
        self._error_label.height = dp(20)
        self._login_btn.height = dp(40)
        Clock.schedule_once(lambda dt: setattr(self._login_btn, "height", dp(48)), 0.3)
