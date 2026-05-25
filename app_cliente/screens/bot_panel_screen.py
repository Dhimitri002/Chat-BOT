"""
Flora Platform — Bot Panel Screen
=====================================
Bot detail panel with status, quick actions, and navigation
to chat, commands, WhatsApp, and settings.
"""
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.metrics import dp

Builder.load_string(
    """
<BotPanelScreen>:
    name: "bot_panel"
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
                text: root.bot_name
                font_size: "18sp"
                bold: True
                color: 1, 1, 1, 1
                text_size: self.width, None
                halign: "left"
                shorten: True
                shorten_from: "right"

            Label:
                text: root.status_emoji
                font_size: "20sp"
                size_hint_x: None
                width: dp(36)

        # Content
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: max(self.minimum_height, root.height - dp(56))
                padding: dp(20)
                spacing: dp(16)

                # Status card
                BoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(100)
                    padding: dp(20)
                    spacing: dp(8)
                    md_bg_color: root.status_card_color
                    radius: [dp(16)]
                    line_color: 0.2, 0.2, 0.3, 0.4
                    line_width: dp(1)

                    Label:
                        text: root.status_title
                        font_size: "18sp"
                        bold: True
                        color: 1, 1, 1, 1
                        size_hint_y: None
                        height: dp(28)
                        text_size: self.width, None
                        halign: "left"

                    Label:
                        text: root.status_desc
                        font_size: "13sp"
                        color: 0.7, 0.7, 0.8, 1
                        text_size: self.width, None
                        halign: "left"

                # Quick actions grid
                GridLayout:
                    cols: 2
                    spacing: dp(12)
                    size_hint_y: None
                    height: dp(200)

                    # WhatsApp
                    MDRaisedButton:
                        text: "WhatsApp"
                        size_hint_y: None
                        height: dp(94)
                        md_bg_color: 0.137, 0.129, 0.243, 0.6
                        text_color: 1, 1, 1, 1
                        line_color: 0.2, 0.2, 0.3, 0.4
                        radius: [dp(16)]
                        font_size: "14sp"
                        on_release: root.go_whatsapp()

                    # Chat test
                    MDRaisedButton:
                        text: "Testar Chat"
                        size_hint_y: None
                        height: dp(94)
                        md_bg_color: 0.137, 0.129, 0.243, 0.6
                        text_color: 1, 1, 1, 1
                        line_color: 0.2, 0.2, 0.3, 0.4
                        radius: [dp(16)]
                        font_size: "14sp"
                        on_release: root.go_chat()

                    # Commands
                    MDRaisedButton:
                        text: "Comandos"
                        size_hint_y: None
                        height: dp(94)
                        md_bg_color: 0.137, 0.129, 0.243, 0.6
                        text_color: 1, 1, 1, 1
                        line_color: 0.2, 0.2, 0.3, 0.4
                        radius: [dp(16)]
                        font_size: "14sp"
                        on_release: root.go_commands()

                    # Settings
                    MDRaisedButton:
                        text: "Configuracoes"
                        size_hint_y: None
                        height: dp(94)
                        md_bg_color: 0.137, 0.129, 0.243, 0.6
                        text_color: 1, 1, 1, 1
                        line_color: 0.2, 0.2, 0.3, 0.4
                        radius: [dp(16)]
                        font_size: "14sp"
                        on_release: root.go_settings()

                # Bot info
                BoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(120)
                    padding: dp(16)
                    spacing: dp(8)
                    md_bg_color: 0.137, 0.129, 0.243, 0.4
                    radius: [dp(14)]

                    Label:
                        text: "Informacoes"
                        font_size: "14sp"
                        bold: True
                        color: 0.914, 0.271, 0.376, 1
                        size_hint_y: None
                        height: dp(24)
                        text_size: self.width, None
                        halign: "left"

                    Label:
                        text: "Personalidade: " + root.bot_personality
                        font_size: "12sp"
                        color: 0.6, 0.6, 0.7, 1
                        text_size: self.width, None
                        halign: "left"

                    Label:
                        text: "Idioma: " + root.bot_language
                        font_size: "12sp"
                        color: 0.6, 0.6, 0.7, 1
                        text_size: self.width, None
                        halign: "left"

                    Label:
                        text: "Criado em: " + root.bot_created
                        font_size: "12sp"
                        color: 0.6, 0.6, 0.7, 1
                        text_size: self.width, None
                        halign: "left"

                Widget:
                    size_hint_y: None
                    height: dp(20)
"""
)


class BotPanelScreen(Screen):
    """Bot detail panel with status and quick actions."""

    bot_name = StringProperty("Bot")
    status_emoji = StringProperty("")
    status_title = StringProperty("Carregando...")
    status_desc = StringProperty("")
    status_card_color = (0.137, 0.129, 0.243, 0.6)
    bot_personality = StringProperty("-")
    bot_language = StringProperty("pt-BR")
    bot_created = StringProperty("-")

    def on_enter(self):
        """Load bot data."""
        app = App.get_running_app()
        bot = getattr(app, "selected_bot", None)
        if bot:
            self._populate(bot)
        else:
            bot_id = getattr(app, "selected_bot_id", None)
            if bot_id:
                self._load_bot(bot_id)

    def _load_bot(self, bot_id):
        """Load bot data from API."""
        try:
            app = App.get_running_app()
            bot = app.api_client.get_bot(bot_id)
            self._populate(bot)
        except Exception:
            pass

    def _populate(self, bot):
        """Populate UI with bot data."""
        self.bot_name = bot.get("name", "Bot")
        self.bot_personality = bot.get("personality", "friendly").capitalize()
        self.bot_language = bot.get("language", "pt-BR")
        created = bot.get("created_at", "")
        if created and isinstance(created, str) and len(created) > 10:
            self.bot_created = created[:10]
        else:
            self.bot_created = "-"

        status = bot.get("status", "disconnected")
        if status == "connected":
            self.status_emoji = ""
            self.status_title = "Conectado"
            self.status_desc = "Seu bot esta ativo e respondendo no WhatsApp"
            self.status_card_color = (0.15, 0.35, 0.25, 0.8)
        elif status == "connecting":
            self.status_emoji = ""
            self.status_title = "Conectando..."
            self.status_desc = "Aguardando conexao com o WhatsApp"
            self.status_card_color = (0.35, 0.3, 0.15, 0.8)
        else:
            self.status_emoji = ""
            self.status_title = "Desconectado"
            self.status_desc = "Conecte ao WhatsApp para comecar a usar"
            self.status_card_color = (0.137, 0.129, 0.243, 0.6)

    def go_back(self):
        self.manager.current = "home"

    def go_whatsapp(self):
        self.manager.current = "whatsapp"

    def go_chat(self):
        self.manager.current = "chat"

    def go_commands(self):
        self.manager.current = "commands"

    def go_settings(self):
        self.manager.current = "settings"
