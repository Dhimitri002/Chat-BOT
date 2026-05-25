"""
Flora Platform — Bot Creation Screen
=======================================
Multi-step bot creation wizard with personality,
welcome message, and configuration options.
"""
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.metrics import dp

PERSONALITIES = [
    ("friendly", "Amigavel", ""),
    ("professional", "Profissional", ""),
    ("funny", "Engracado", ""),
    ("formal", "Formal", ""),
    ("cute", "Fofo", ""),
]

Builder.load_string(
    """
<BotCreateScreen>:
    name: "bot_create"
    canvas.before:
        Color:
            rgba: 0.102, 0.102, 0.18, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: "vertical"

        # Top bar
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(16), dp(8)
            spacing: dp(12)

            MDFlatButton:
                text: "Voltar"
                size_hint_x: None
                width: dp(80)
                text_color: 0.7, 0.7, 0.8, 1
                on_release: root.go_back()

            Label:
                text: "Novo Bot"
                font_size: "18sp"
                bold: True
                color: 1, 1, 1, 1
                text_size: self.width, None
                halign: "left"

            Label:
                text: str(root.step) + "/3"
                font_size: "14sp"
                color: 0.5, 0.5, 0.6, 1
                size_hint_x: None
                width: dp(40)

        # Step 1: Basic Info
        BoxLayout:
            orientation: "vertical"
            padding: dp(24)
            spacing: dp(16)
            opacity: 1 if root.step == 1 else 0
            size_hint_y: 1 if root.step == 1 else 0

            Label:
                text: "Informacoes basicas"
                font_size: "22sp"
                bold: True
                color: 1, 1, 1, 1
                size_hint_y: None
                height: dp(32)
                text_size: self.width, None
                halign: "left"

            Label:
                text: "Dê um nome e descricao para seu bot"
                font_size: "13sp"
                color: 0.6, 0.6, 0.7, 1
                size_hint_y: None
                height: dp(24)
                text_size: self.width, None
                halign: "left"

            MDTextField:
                id: bot_name_field
                hint_text: "Nome do bot"
                icon_left: "robot"
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

            MDTextField:
                id: bot_desc_field
                hint_text: "Descricao (opcional)"
                icon_left: "text"
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

        # Step 2: Personality
        BoxLayout:
            orientation: "vertical"
            padding: dp(24)
            spacing: dp(12)
            opacity: 1 if root.step == 2 else 0
            size_hint_y: 1 if root.step == 2 else 0

            Label:
                text: "Personalidade"
                font_size: "22sp"
                bold: True
                color: 1, 1, 1, 1
                size_hint_y: None
                height: dp(32)
                text_size: self.width, None
                halign: "left"

            Label:
                text: "Como seu bot deve se comportar?"
                font_size: "13sp"
                color: 0.6, 0.6, 0.7, 1
                size_hint_y: None
                height: dp(24)
                text_size: self.width, None
                halign: "left"

            GridLayout:
                id: personality_grid
                cols: 2
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height

        # Step 3: Welcome Message
        BoxLayout:
            orientation: "vertical"
            padding: dp(24)
            spacing: dp(16)
            opacity: 1 if root.step == 3 else 0
            size_hint_y: 1 if root.step == 3 else 0

            Label:
                text: "Mensagem de boas-vindas"
                font_size: "22sp"
                bold: True
                color: 1, 1, 1, 1
                size_hint_y: None
                height: dp(32)
                text_size: self.width, None
                halign: "left"

            Label:
                text: "Mensagem enviada quando alguem iniciar conversa"
                font_size: "13sp"
                color: 0.6, 0.6, 0.7, 1
                size_hint_y: None
                height: dp(24)
                text_size: self.width, None
                halign: "left"

            MDTextField:
                id: welcome_field
                text: "Ola! Como posso te ajudar?"
                hint_text: "Mensagem de boas-vindas"
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

            MDTextField:
                id: farewell_field
                text: "Ate mais! Volte sempre."
                hint_text: "Mensagem de despedida"
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

        Widget:
            size_hint_y: 0.1

        # Bottom buttons
        BoxLayout:
            size_hint_y: None
            height: dp(64)
            padding: dp(20)
            spacing: dp(12)

            MDRaisedButton:
                text: "Anterior"
                size_hint_x: 0.4
                size_hint_y: None
                height: dp(48)
                md_bg_color: 0.137, 0.129, 0.243, 0.6
                text_color: 0.7, 0.7, 0.8, 1
                line_color: 0.2, 0.2, 0.3, 1
                radius: [dp(14)]
                on_release: root.prev_step()
                opacity: 0 if root.step == 1 else 1
                disabled: root.step == 1

            MDRaisedButton:
                text: root.next_text
                size_hint_x: 0.6
                size_hint_y: None
                height: dp(48)
                font_size: "15sp"
                bold: True
                md_bg_color: 0.914, 0.271, 0.376, 1
                text_color: 1, 1, 1, 1
                line_color: 0.914, 0.271, 0.376, 1
                radius: [dp(14)]
                on_release: root.next_step()
"""
)


class BotCreateScreen(Screen):
    """Multi-step bot creation wizard."""

    step = NumericProperty(1)
    next_text = StringProperty("Proximo")
    selected_personality = StringProperty("friendly")
    is_loading = BooleanProperty(False)

    def on_enter(self):
        """Reset wizard state."""
        self.step = 1
        self.is_loading = False
        if "bot_name_field" in self.ids:
            self.ids.bot_name_field.text = ""
            self.ids.bot_desc_field.text = ""
            self.ids.welcome_field.text = "Ola! Como posso te ajudar?"
            self.ids.farewell_field.text = "Ate mais! Volte sempre."
        self._build_personality_grid()

    def _build_personality_grid(self):
        """Build personality selection grid."""
        if "personality_grid" not in self.ids:
            return
        grid = self.ids.personality_grid
        grid.clear_widgets()
        for key, label, emoji in PERSONALITIES:
            btn = Button(
                text=f"{emoji}\n{label}",
                size_hint_y=None,
                height=dp(64),
                background_color=(0.137, 0.129, 0.243, 0.6),
                color=(1, 1, 1, 1),
                font_size="13sp",
                halign="center",
            )
            btn.personality_key = key
            btn.bind(on_release=lambda b: self._select_personality(b.personality_key))
            grid.add_widget(btn)

    def _select_personality(self, key):
        """Select a personality."""
        self.selected_personality = key

    def next_step(self):
        """Advance to next step or create bot."""
        if self.step == 1:
            name = self.ids.bot_name_field.text.strip()
            if not name:
                return
        if self.step < 3:
            self.step += 1
            self.next_text = "Criar Bot" if self.step == 3 else "Proximo"
        else:
            self._create_bot()

    def prev_step(self):
        """Go back one step."""
        if self.step > 1:
            self.step -= 1
            self.next_text = "Proximo"

    def _create_bot(self):
        """Submit bot creation to API."""
        if self.is_loading:
            return
        self.is_loading = True

        name = self.ids.bot_name_field.text.strip()
        desc = self.ids.bot_desc_field.text.strip()
        welcome = self.ids.welcome_field.text.strip() or "Ola! Como posso te ajudar?"
        farewell = self.ids.farewell_field.text.strip() or "Ate mais!"

        data = {
            "name": name,
            "description": desc,
            "personality": self.selected_personality,
            "welcome_message": welcome,
            "farewell_message": farewell,
        }

        import threading

        def _thread():
            from kivy.clock import mainthread

            @mainthread
            def _on_success(result):
                self.is_loading = False
                app = App.get_running_app()
                app.selected_bot_id = result.get("id")
                app.selected_bot = result
                self.manager.current = "whatsapp"

            @mainthread
            def _on_error(err):
                self.is_loading = False

            try:
                app = App.get_running_app()
                result = app.api_client.create_bot(data)
                _on_success(result)
            except Exception as e:
                _on_error(e)

        thread = threading.Thread(target=_thread)
        thread.daemon = True
        thread.start()

    def go_back(self):
        """Go back to home."""
        self.manager.current = "home"


from kivy.uix.button import Button
