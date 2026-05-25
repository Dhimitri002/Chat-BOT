"""
Flora Platform — Register Screen
===================================
New account registration with name, email, password, and
license key validation.
"""
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.metrics import dp

Builder.load_string(
    """
<RegisterScreen>:
    name: "register"
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
            spacing: dp(14)

            # Spacer
            Widget:
                size_hint_y: None
                height: dp(40)

            # Back button
            MDRaisedButton:
                text: "Voltar"
                size_hint_x: None
                width: dp(80)
                size_hint_y: None
                height: dp(36)
                md_bg_color: 0.137, 0.129, 0.243, 0.6
                text_color: 0.7, 0.7, 0.8, 1
                line_color: 0.2, 0.2, 0.3, 1
                radius: [dp(10)]
                on_release: root.go_back()

            # Logo
            Label:
                text: ""
                font_size: "42sp"
                size_hint_y: None
                height: dp(50)

            Label:
                text: "Crie sua conta"
                font_size: "26sp"
                bold: True
                color: 1, 1, 1, 1
                size_hint_y: None
                height: dp(36)

            Label:
                text: "Comece a criar chatbots incríveis"
                font_size: "13sp"
                color: 0.6, 0.6, 0.7, 1
                size_hint_y: None
                height: dp(22)

            # Error message
            Label:
                text: root.error_message
                font_size: "12sp"
                color: 0.914, 0.271, 0.376, 1
                size_hint_y: None
                height: dp(20) if root.error_message else dp(0)
                opacity: 1 if root.error_message else 0

            # Name
            MDTextField:
                id: name_field
                hint_text: "Seu nome"
                icon_left: "account"
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

            # Email
            MDTextField:
                id: email_field
                hint_text: "Email"
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
                hint_text: "Senha (min. 6 caracteres)"
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

            # License key
            MDTextField:
                id: license_field
                hint_text: "Chave de licenca"
                icon_left: "key"
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

            # Register button
            MDRaisedButton:
                text: "  Criar conta  "
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
                on_release: root.do_register()
                disabled: root.is_loading

            # Loading
            Label:
                text: "Criando conta..." if root.is_loading else ""
                font_size: "12sp"
                color: 0.6, 0.6, 0.7, 1
                size_hint_y: None
                height: dp(20)

            Widget:
                size_hint_y: None
                height: dp(32)
"""
)


class RegisterScreen(Screen):
    """Registration screen for new accounts."""

    is_loading = BooleanProperty(False)
    error_message = ""

    def on_enter(self):
        """Reset form on enter."""
        self.error_message = ""
        self.is_loading = False
        for field_id in ("name_field", "email_field", "password_field", "license_field"):
            if field_id in self.ids:
                self.ids[field_id].text = ""

    def do_register(self):
        """Perform registration with validation."""
        name = self.ids.name_field.text.strip()
        email = self.ids.email_field.text.strip()
        password = self.ids.password_field.text
        license_key = self.ids.license_field.text.strip()

        if not name:
            self.error_message = "Por favor, insira seu nome"
            return
        if not email or "@" not in email:
            self.error_message = "Email invalido"
            return
        if not password or len(password) < 6:
            self.error_message = "Senha deve ter pelo menos 6 caracteres"
            return
        if not license_key:
            self.error_message = "Chave de licenca obrigatoria"
            return

        self.error_message = ""
        self.is_loading = True

        import threading
        thread = threading.Thread(
            target=self._register_thread,
            args=(email, password, name, license_key),
        )
        thread.daemon = True
        thread.start()

    def _register_thread(self, email, password, name, license_key):
        """Background registration thread."""
        from kivy.clock import mainthread

        @mainthread
        def _on_success(result):
            self.is_loading = False
            self.error_message = ""
            self.manager.current = "onboarding"

        @mainthread
        def _on_error(err):
            self.is_loading = False
            self.error_message = str(err) if str(err) else "Erro ao criar conta"

        try:
            app = App.get_running_app()
            auth = app.auth_service
            result = auth.register(email, password, name, license_key)
            _on_success(result)
        except Exception as e:
            _on_error(e)

    def go_back(self):
        """Navigate back to login."""
        self.manager.current = "login"
