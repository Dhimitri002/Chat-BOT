"""
Flora Platform — Home Screen
===============================
Main dashboard with bot list, quick actions, and user greeting.
"""
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ListProperty, StringProperty, BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.metrics import dp

Builder.load_string(
    """
<BotCard>:
    size_hint_y: None
    height: dp(100)
    padding: dp(16)
    spacing: dp(12)
    md_bg_color: 0.137, 0.129, 0.243, 0.6
    radius: [dp(16)]
    line_color: 0.2, 0.2, 0.3, 0.4
    line_width: dp(1)

    BoxLayout:
        orientation: "vertical"
        spacing: dp(4)

        BoxLayout:
            spacing: dp(8)
            Label:
                text: root.bot_emoji
                font_size: "24sp"
                size_hint_x: None
                width: dp(36)
            Label:
                text: root.bot_name
                font_size: "16sp"
                bold: True
                color: 1, 1, 1, 1
                text_size: self.width, None
                halign: "left"
                shorten: True
                shorten_from: "right"

        BoxLayout:
            spacing: dp(8)
            size_hint_y: None
            height: dp(20)
            Label:
                text: root.status_text
                font_size: "11sp"
                color: root.status_color
                text_size: self.width, None
                halign: "left"
            Widget:
            Label:
                text: root.bot_status_badge
                font_size: "10sp"
                color: 0.6, 0.6, 0.7, 1
                size_hint_x: None
                width: dp(80)
                text_size: self.width, None
                halign: "right"

<HomeScreen>:
    name: "home"
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
            height: dp(64)
            padding: dp(20), dp(12)
            spacing: dp(12)

            # User greeting
            BoxLayout:
                orientation: "vertical"
                Label:
                    text: root.greeting_text
                    font_size: "13sp"
                    color: 0.6, 0.6, 0.7, 1
                    text_size: self.width, None
                    halign: "left"
                    size_hint_y: 0.4
                Label:
                    text: root.user_name
                    font_size: "18sp"
                    bold: True
                    color: 1, 1, 1, 1
                    text_size: self.width, None
                    halign: "left"
                    size_hint_y: 0.6

            # Flora AI button
            MDRaisedButton:
                text: ""
                size_hint_x: None
                width: dp(44)
                size_hint_y: None
                height: dp(44)
                pos_hint: {"center_y": 0.5}
                md_bg_color: 0.137, 0.129, 0.243, 0.8
                text_color: 1, 1, 1, 1
                line_color: 0.2, 0.2, 0.3, 0.5
                radius: [dp(12)]
                font_size: "22sp"
                on_release: root.go_flora()

        # Scroll content
        ScrollView:
            do_scroll_x: False
            bar_width: dp(4)
            bar_color: 0.914, 0.271, 0.376, 0.5
            bar_inactive_color: 0.2, 0.2, 0.3, 0.3

            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: max(self.minimum_height, root.height - dp(64))
                padding: dp(20)
                spacing: dp(16)

                # Quick actions
                BoxLayout:
                    size_hint_y: None
                    height: dp(80)
                    spacing: dp(12)

                    # Create bot
                    MDRaisedButton:
                        text: "Novo Bot"
                        size_hint_x: 0.5
                        md_bg_color: 0.914, 0.271, 0.376, 1
                        text_color: 1, 1, 1, 1
                        line_color: 0.914, 0.271, 0.376, 1
                        radius: [dp(14)]
                        font_size: "14sp"
                        bold: True
                        on_release: root.go_create_bot()

                    # Plans
                    MDRaisedButton:
                        text: "Planos"
                        size_hint_x: 0.5
                        md_bg_color: 0.137, 0.129, 0.243, 0.8
                        text_color: 0.914, 0.271, 0.376, 1
                        line_color: 0.2, 0.2, 0.3, 0.5
                        radius: [dp(14)]
                        font_size: "14sp"
                        on_release: root.go_plans()

                # Section title
                BoxLayout:
                    size_hint_y: None
                    height: dp(30)
                    Label:
                        text: "Seus Bots"
                        font_size: "16sp"
                        bold: True
                        color: 1, 1, 1, 1
                        text_size: self.width, None
                        halign: "left"
                    Label:
                        text: str(root.bot_count) + " bots"
                        font_size: "12sp"
                        color: 0.5, 0.5, 0.6, 1
                        text_size: self.width, None
                        halign: "right"

                # Bot list
                GridLayout:
                    id: bot_list
                    cols: 1
                    spacing: dp(10)
                    size_hint_y: None
                    height: self.minimum_height

                # Empty state
                BoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(160)
                    padding: dp(20)
                    spacing: dp(8)
                    opacity: 1 if root.show_empty else 0

                    Label:
                        text: ""
                        font_size: "48sp"
                        size_hint_y: None
                        height: dp(60)
                    Label:
                        text: "Nenhum bot criado ainda"
                        font_size: "15sp"
                        color: 0.6, 0.6, 0.7, 1
                    Label:
                        text: "Toque em 'Novo Bot' para comecar"
                        font_size: "12sp"
                        color: 0.4, 0.4, 0.5, 1

                # Bottom spacer
                Widget:
                    size_hint_y: None
                    height: dp(20)

        # Bottom nav
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            md_bg_color: 0.137, 0.129, 0.243, 0.8
            spacing: dp(4)

            # Home (active)
            BoxLayout:
                orientation: "vertical"
                spacing: dp(2)
                padding: dp(4)
                Label:
                    text: ""
                    font_size: "20sp"
                    color: 0.914, 0.271, 0.376, 1
                Label:
                    text: "Inicio"
                    font_size: "10sp"
                    color: 0.914, 0.271, 0.376, 1

            # Bots
            BoxLayout:
                orientation: "vertical"
                spacing: dp(2)
                padding: dp(4)
                on_release: root.go_create_bot()
                Label:
                    text: ""
                    font_size: "20sp"
                    color: 0.5, 0.5, 0.6, 1
                Label:
                    text: "Bots"
                    font_size: "10sp"
                    color: 0.5, 0.5, 0.6, 1

            # Flora
            BoxLayout:
                orientation: "vertical"
                spacing: dp(2)
                padding: dp(4)
                on_release: root.go_flora()
                Label:
                    text: ""
                    font_size: "20sp"
                    color: 0.5, 0.5, 0.6, 1
                Label:
                    text: "Flora"
                    font_size: "10sp"
                    color: 0.5, 0.5, 0.6, 1

            # Settings
            BoxLayout:
                orientation: "vertical"
                spacing: dp(2)
                padding: dp(4)
                on_release: root.go_settings()
                Label:
                    text: ""
                    font_size: "20sp"
                    color: 0.5, 0.5, 0.6, 1
                Label:
                    text: "Config"
                    font_size: "10sp"
                    color: 0.5, 0.5, 0.6, 1
"""
)


class BotCard(BoxLayout):
    """Card widget for displaying a bot in the list."""
    bot_name = StringProperty("")
    bot_emoji = StringProperty("")
    status_text = StringProperty("")
    status_color = (0.5, 0.5, 0.6, 1)
    bot_status_badge = StringProperty("")


class HomeScreen(Screen):
    """Main home screen with bot list and quick actions."""

    greeting_text = StringProperty("Ola,")
    user_name = StringProperty("Usuario")
    bot_count = 0
    show_empty = BooleanProperty(True)
    bots = ListProperty([])

    def on_enter(self):
        """Load data when entering screen."""
        self._load_user_info()
        self._load_bots()

    def _load_user_info(self):
        """Load user info from auth service."""
        try:
            app = App.get_running_app()
            auth = app.auth_service
            if auth and auth.user:
                self.user_name = auth.user_name
                self.greeting_text = self._get_greeting()
        except Exception:
            pass

    def _get_greeting(self) -> str:
        """Get time-based greeting."""
        from datetime import datetime
        hour = datetime.now().hour
        if hour < 12:
            return "Bom dia,"
        elif hour < 18:
            return "Boa tarde,"
        return "Boa noite,"

    def _load_bots(self):
        """Load bot list from API."""
        try:
            app = App.get_running_app()
            resp = app.api_client.list_bots()
            bots = resp.get("bots", [])
            self.bots = bots
            self.bot_count = len(bots)
            self.show_empty = len(bots) == 0
            self._render_bot_list(bots)
        except Exception as e:
            self.show_empty = True
            self.bot_count = 0

    def _render_bot_list(self, bots):
        """Render bot cards in the list."""
        grid = self.ids.bot_list
        grid.clear_widgets()
        for bot in bots:
            card = BotCard()
            card.bot_name = bot.get("name", "Bot sem nome")
            card.bot_emoji = ""
            status = bot.get("status", "unknown")
            if status == "connected":
                card.status_text = "Conectado"
                card.status_color = (0.31, 0.8, 0.639, 1)
                card.bot_status_badge = "Online"
            elif status == "connecting":
                card.status_text = "Conectando..."
                card.status_color = (0.95, 0.77, 0.06, 1)
                card.bot_status_badge = "Pendente"
            else:
                card.status_text = "Desconectado"
                card.status_color = (0.5, 0.5, 0.6, 1)
                card.bot_status_badge = "Offline"
            card.bind(on_release=lambda b, bot=bot: self._open_bot(bot))
            grid.add_widget(card)

    def _open_bot(self, bot):
        """Open bot panel for a specific bot."""
        app = App.get_running_app()
        app.selected_bot_id = bot.get("id")
        app.selected_bot = bot
        self.manager.current = "bot_panel"

    def go_create_bot(self):
        """Navigate to bot creation screen."""
        self.manager.current = "bot_create"

    def go_plans(self):
        """Navigate to plans screen."""
        self.manager.current = "plans"

    def go_flora(self):
        """Navigate to Flora AI chat screen."""
        self.manager.current = "flora_chat"

    def go_settings(self):
        """Navigate to settings screen."""
        self.manager.current = "settings"
