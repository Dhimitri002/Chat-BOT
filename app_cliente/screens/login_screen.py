"""
Flora Platform — Login Screen
================================
Clean login screen with email/password fields,
license key option, and smooth animations.
"""
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.metrics import dp

Builder.load_string(
    """
<LoginScreen>:
    name: "login"
    canvas.before:
        Color:
            rgba: 0.102, 0.102, 0.18, 1
        Rectangle:
            pos: self.pos
            size: self.size

    ScrollView:
        do_scroll_x: False
        BoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: max(self.minimum_height, root.height)
            padding: dp(32)
            spacing: dp(16)

            # Spacer
            Widget:
                size_hint_y: None
                height: dp(60)

            # Logo
            Label:
                text: ""
                font_size: "56sp"
                size_hint_y: None
                height: dp(70)

            Label:
                text: "Bem-vindo de volta"
                font_size: "28sp"
                bold: True
                color: 1, 1, 1, 1
                size_hint_y: None
                height: dp(40)

            Label:
                text: "Entre na sua conta Flora"
                font_size: "14sp"
                color: 0.6, 0.6, 0.7, 1
                size_hint_y: None
                height: dp(24)

            # Error message
            Label:
                text: root.error_message
                font_size: "12sp"
                color: 0.914, 0.271, 0.376, 1
                size_hint_y: None
                height: dp(20) if root.error_message else dp(0)
                opacity: 1 if root.error_message else 0

            # Spacer
            Widget:
                size_hint_y: None
                height: dp(16)

            # Email
            MDTextField:
                id: email_field
                hint_text: "Email"
                text: root.email_text
                icon_left: "email"
                mode: "round"
                size_hint_y: None
                height: dp(52)
                line_color_normal: 0.137, 0.129, 0.243, 1
                line_color_focus: 0.914, 0.271, 0.376, 1
                hint_text_color_normal: 0.5, 0.5, 0.6, 1
                text_color_normal: 1, 1, 1, 1
                text_color_focus: 1, 1, 1, 1
                icon_color_normal: 0.6, 0.6, 0.7, 1
                icon_color_focus: 0.914, 0.271, 0.376, 1
                fill_color_normal: 0.137, 0.129, 0.243, 0.6
                fill_color_focus: 0.137, 0.129, 0.243, 0.9

            # Password
            MDTextField:
                id: password_field
                hint_text: "Senha"
                text: root.password_text
                password: True
                icon_left: "lock"
                mode: "round"
                size_hint_y: None
                height: dp(52)
                line_color_normal: 0.137, 0.129, 0.243, 1
                line_color_focus: 0.914, 0.271, 0.376, 1
                hint_text_color_normal: 0.5, 0.5, 0.6, 1
                text_color_normal: 1, 1, 1, 1
                text_color_focus: 1, 1, 1, 1
                icon_color_normal: 0.6, 0.6, 0.7, 1
                icon_color_focus: 0.914, 0.271, 0.376, 1
                fill_color_normal: 0.137, 0.129, 0.243, 0.6
                fill_color_focus: 0.137, 0.129, 0.243, 0.9

            # Login button
            MDRaisedButton:
                text: "  Entrar  "
                font_size: "16sp"
                bold: True
                pos_hint: {"center_x": 0.5}
                size_hint_y: None
                height: dp(52)
                size_hint_x: 1
                md_bg_color: 0.914, 0.271, 0.376, 1
                text_color: 1, 1, 1, 1
                line_color: 0.914, 0.271, 0.376, 1
                radius: [dp(14)]
                on_release: root.do_login()
                disabled: root.is_loading

            # Loading indicator
            Label:
                text: "Entrando..." if root.is_loading else ""
                font_size: "12sp"
                color: 0.6, 0.6, 0.7, 1
                size_hint_y: None
                height: dp(20)

            Widget:
                size_hint_y: None
                height: dp(8)

            # Divider
            BoxLayout:
                size_hint_y: None
                height: dp(24)
                padding: dp(40), 0
                Widget:
                    size_hint_y: None
                    height: dp(1)
                    canvas.before:
                        Color:
                            rgba: 0.3, 0.3, 0.4, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size
                Label:
                    text: "ou"
                    font_size: "12sp"
                    color: 0.5, 0.5, 0.6, 1
                    size_hint_x: None
                    width: dp(30)
                    size_hint_y: None
                    height: dp(24)
                Widget:
                    size_hint_y: None
                    height: dp(1)
                    canvas.before:
                        Color:
                            rgba: 0.3, 0.3, 0.4, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size

            # Register button
            MDFlatButton:
                text: "Criar nova conta"
                font_size: "14sp"
                pos_hint: {"center_x": 0.5}
                size_hint_y: None
                height: dp(44)
                text_color: 0.914, 0.271, 0.376, 1
                on_release: root.go_register()

            Widget:
                size_hint_y: None
                height: dp(32)
"""
)


class LoginScreen(Screen):
    """Login screen with email and password authentication."""

    is_loading = BooleanProperty(False)
    error_message = ""
    email_text = ""
    password_text = ""

    def on_enter(self):
        """Reset form when entering screen."""
        self.error_message = ""
        self.is_loading = False
        self.email_text = ""
        self.password_text = ""

    def do_login(self):
        """Perform login with validation."""
        email = self.ids.email_field.text.strip()
        password = self.ids.password_field.text

        # Validation
        if not email:
            self.error_message = "Por favor, insira seu email"
            return
        if not password:
            self.error_message = "Por favor, insira sua senha"
            return
        if "@" not in email:
            self.error_message = "Email invalido"
            return

        self.error_message = ""
        self.is_loading = True

        # Run login in background thread
        import threading
        thread = threading.Thread(target=self._login_thread, args=(email, password))
        thread.daemon = True
        thread.start()

    def _login_thread(self, email, password):
        """Background login thread."""
        from kivy.clock import mainthread

        @mainthread
        def _on_success(result):
            self.is_loading = False
            self.error_message = ""
            self.manager.current = "home"

        @mainthread
        def _on_error(err):
            self.is_loading = False
            self.error_message = str(err) if str(err) else "Erro ao fazer login"

        try:
            app = App.get_running_app()
            auth = app.auth_service
            result = auth.login(email, password)
            _on_success(result)
        except Exception as e:
            _on_error(e)

    def go_register(self):
        """Navigate to register screen."""
        self.manager.current = "register"
