"""
Flora Platform — Chat Screen
================================
Test chat interface for sending messages to a bot
and viewing responses.
"""
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.metrics import dp

Builder.load_string(
    """
<ChatBubble>:
    size_hint_y: None
    height: self.minimum_height
    padding: dp(12), dp(8)
    spacing: dp(8)

    BoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: self.minimum_height
        spacing: dp(2)

        Label:
            id: msg_text
            text: root.message_text
            font_size: "14sp"
            color: 1, 1, 1, 1
            text_size: self.width, None
            halign: "left"
            valign: "top"
            size_hint_y: None
            height: self.texture_size[1]

        Label:
            id: msg_time
            text: root.message_time
            font_size: "10sp"
            color: 0.5, 0.5, 0.6, 1
            size_hint_y: None
            height: dp(14)
            text_size: self.width, None
            halign: "right"

<ChatScreen>:
    name: "chat"
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
                text: "Testar: " + root.bot_name
                font_size: "16sp"
                bold: True
                color: 1, 1, 1, 1
                text_size: self.width, None
                halign: "left"
                shorten: True
                shorten_from: "right"

        # Chat messages area
        ScrollView:
            id: chat_scroll
            do_scroll_x: False
            bar_width: dp(4)
            bar_color: 0.914, 0.271, 0.376, 0.5

            BoxLayout:
                id: messages_container
                orientation: "vertical"
                size_hint_y: None
                height: max(self.minimum_height, root.height - dp(120))
                padding: dp(16)
                spacing: dp(10)

        # Input area
        BoxLayout:
            size_hint_y: None
            height: dp(64)
            padding: dp(12), dp(8)
            spacing: dp(8)
            md_bg_color: 0.137, 0.129, 0.243, 0.6

            MDTextField:
                id: message_input
                hint_text: "Digite sua mensagem..."
                mode: "round"
                size_hint_x: 0.8
                size_hint_y: None
                height: dp(48)
                line_color_normal: 0.2, 0.2, 0.3, 0.5
                line_color_focus: 0.914, 0.271, 0.376, 1
                hint_text_color_normal: 0.4, 0.4, 0.5, 1
                text_color_normal: 1, 1, 1, 1
                text_color_focus: 1, 1, 1, 1
                fill_color_normal: 0.102, 0.102, 0.18, 0.8
                fill_color_focus: 0.102, 0.102, 0.18, 1
                on_text_validate: root.send_message()

            MDRaisedButton:
                text: ""
                size_hint_x: None
                width: dp(48)
                size_hint_y: None
                height: dp(48)
                md_bg_color: 0.914, 0.271, 0.376, 1
                text_color: 1, 1, 1, 1
                line_color: 0.914, 0.271, 0.376, 1
                radius: [dp(12)]
                font_size: "20sp"
                on_release: root.send_message()
"""
)


class ChatBubble(BoxLayout):
    """Chat message bubble widget."""
    message_text = StringProperty("")
    message_time = StringProperty("")

    def __init__(self, text="", time_str="", is_user=False, **kwargs):
        super().__init__(**kwargs)
        self.message_text = text
        self.message_time = time_str
        if is_user:
            self.md_bg_color = (0.914, 0.271, 0.376, 0.3)
        else:
            self.md_bg_color = (0.137, 0.129, 0.243, 0.6)
        self.radius = [dp(14)]


class ChatScreen(Screen):
    """Test chat screen for bot testing."""

    bot_name = StringProperty("Bot")

    def on_enter(self):
        """Load bot info and chat history."""
        app = App.get_running_app()
        bot = getattr(app, "selected_bot", None)
        if bot:
            self.bot_name = bot.get("name", "Bot")
        self._load_history()
        self._add_system_message("Envie uma mensagem para testar seu bot!")

    def _load_history(self):
        """Load chat history from API."""
        try:
            app = App.get_running_app()
            bot_id = getattr(app, "selected_bot_id", None)
            if not bot_id:
                return
            resp = app.api_client.get_chat_history(bot_id)
            messages = resp.get("messages", resp if isinstance(resp, list) else [])
            for msg in messages:
                is_user = msg.get("role") == "user"
                text = msg.get("text", msg.get("content", ""))
                time_str = msg.get("created_at", "")[:16] if msg.get("created_at") else ""
                self._add_bubble(text, time_str, is_user)
        except Exception:
            pass

    def _add_system_message(self, text):
        """Add a system/info message."""
        container = self.ids.messages_container
        label = Label(
            text=text,
            font_size="12sp",
            color=(0.5, 0.5, 0.6, 1),
            size_hint_y=None,
            height=dp(30),
            halign="center",
        )
        container.add_widget(label)

    def _add_bubble(self, text, time_str="", is_user=False):
        """Add a chat bubble."""
        container = self.ids.messages_container
        bubble = ChatBubble(text=text, time_str=time_str, is_user=is_user)
        container.add_widget(bubble)
        # Scroll to bottom
        Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)

    def _scroll_to_bottom(self):
        """Scroll chat to bottom."""
        if "chat_scroll" in self.ids:
            self.ids.chat_scroll.scroll_y = 0

    def send_message(self):
        """Send a message to the bot."""
        if "message_input" not in self.ids:
            return
        text = self.ids.message_input.text.strip()
        if not text:
            return

        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M")

        # Add user bubble
        self._add_bubble(text, time_str, is_user=True)
        self.ids.message_input.text = ""

        # Send to API
        app = App.get_running_app()
        bot_id = getattr(app, "selected_bot_id", None)
        if not bot_id:
            return

        import threading

        def _thread():
            from kivy.clock import mainthread

            @mainthread
            def _on_success(result):
                reply = result.get("reply", result.get("text", "Sem resposta"))
                from datetime import datetime
                t = datetime.now().strftime("%H:%M")
                self._add_bubble(reply, t, is_user=False)

            @mainthread
            def _on_error(err):
                self._add_bubble("Erro: " + str(err), "", is_user=False)

            try:
                result = app.api_client.send_message(bot_id, text)
                _on_success(result)
            except Exception as e:
                _on_error(e)

        thread = threading.Thread(target=_thread)
        thread.daemon = True
        thread.start()

    def go_back(self):
        self.manager.current = "bot_panel"


from kivy.uix.label import Label
