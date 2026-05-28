# ═══════════════════════════════════════════════════════════════
# Flora Platform — Chat Screen
# ═══════════════════════════════════════════════════════════════

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.progressindicator import MDCircularProgressIndicator


class ChatBubble(MDCard):
    """A chat message bubble."""

    def __init__(self, text: str, is_sent: bool, timestamp: str = "", **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(None, None),
            radius=[dp(16)],
            padding=[dp(12), dp(8)],
            elevation=1,
            **kwargs,
        )

        if is_sent:
            self.md_bg_color = (0.424, 0.388, 1.0, 1)
            self.pos_hint = {"right": 0.95}
            self.size_hint_x = 0.75
        else:
            self.md_bg_color = (0.2, 0.23, 0.35, 1)
            self.pos_hint = {"x": 0.05}
            self.size_hint_x = 0.75

        # Message text
        msg_label = MDLabel(
            text=text,
            font_style="Body",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            adaptive_height=True,
            text_size=(dp(240), None),
        )
        msg_label.bind(texture_size=lambda *x: msg_label.setter('height')(msg_label, msg_label.texture_size[1]))
        self.add_widget(msg_label)

        # Timestamp
        if timestamp:
            time_label = MDLabel(
                text=timestamp,
                font_style="Label",
                role="small",
                halign="right" if is_sent else "left",
                theme_text_color="Custom",
                text_color=(0.7, 0.7, 0.75, 0.7) if is_sent else (0.5, 0.5, 0.55, 0.7),
                size_hint_y=None,
                height=dp(16),
            )
            self.add_widget(time_label)

        # Set height
        self.bind(minimum_height=self.setter('height'))


class ChatScreen(MDScreen):
    """Chat interface for testing the bot."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = []
        self._build_ui()

    def _build_ui(self):
        self.md_bg_color = (0.102, 0.102, 0.180, 1)

        layout = MDFloatLayout()

        # Top bar
        top_bar = MDBoxLayout(
            size_hint=(1, None),
            height=dp(56),
            pos_hint={"top": 1},
            padding=[dp(8), dp(4)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            elevation=4,
        )
        back_btn = MDIconButton(
            icon="arrow-left",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
            on_release=self._on_back,
        )
        top_bar.add_widget(back_btn)
        top_bar.add_widget(MDLabel(
            text="💬 Chat do Bot",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        ))
        layout.add_widget(top_bar)

        # Messages area
        self.scroll = MDScrollView(
            pos_hint={"top": 0.92},
            size_hint=(1, 0.82),
            do_scroll_x=False,
            bar_width=dp(4),
            bar_color=(0.424, 0.388, 1.0, 0.3),
        )

        self.messages_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(12), dp(8), dp(12), dp(80)],
            size_hint_y=None,
            adaptive_height=True,
        )

        # Welcome message
        welcome_bubble = ChatBubble(
            text="Ola! 👋 Este e o chat de teste do seu bot. Envie uma mensagem e veja como ele responde!",
            is_sent=False,
        )
        self.messages_layout.add_widget(welcome_bubble)

        self.scroll.add_widget(self.messages_layout)
        layout.add_widget(self.scroll)

        # Typing indicator (hidden)
        self.typing_box = MDBoxLayout(
            size_hint=(1, None),
            height=dp(36),
            pos_hint={"y": 0.1},
            padding=[dp(16), 0],
            opacity=0,
        )
        typing_card = MDCard(
            size_hint=(None, None),
            size=(dp(70), dp(30)),
            radius=[dp(15)],
            md_bg_color=(0.2, 0.23, 0.35, 1),
            padding=[dp(12), dp(4)],
        )
        typing_dots = MDLabel(
            text="...",
            font_style="Title",
            role="small",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        )
        typing_card.add_widget(typing_dots)
        self.typing_box.add_widget(typing_card)
        layout.add_widget(self.typing_box)

        # Input area
        input_box = MDBoxLayout(
            size_hint=(1, None),
            height=dp(64),
            pos_hint={"y": 0},
            padding=[dp(12), dp(6), dp(12), dp(6)],
            spacing=dp(8),
            md_bg_color=(0.13, 0.16, 0.28, 1),
            elevation=8,
        )

        self.msg_input = MDTextField(
            mode="outlined",
            hint_text="Digite sua mensagem...",
            size_hint_x=0.8,
            line_color_focus=(0.424, 0.388, 1.0, 1),
            line_color_normal=(0.3, 0.3, 0.4, 1),
            text_color_normal=(0.7, 0.7, 0.75, 1),
            text_color_focus=(1, 1, 1, 1),
            fill_color_normal=(0.1, 0.1, 0.16, 1),
            radius=[dp(24)],
        )
        input_box.add_widget(self.msg_input)

        send_btn = MDIconButton(
            icon="send",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            icon_size=sp(24),
            on_release=self._on_send,
        )
        input_box.add_widget(send_btn)

        layout.add_widget(input_box)
        self.add_widget(layout)

    def on_enter(self):
        """Load chat history when entering."""
        self._load_history()

    def _load_history(self):
        """Load chat history from API."""
        from apps.client.main import get_stored_token, get_stored_bot_id, api_request_async
        token = get_stored_token()
        bot_id = get_stored_bot_id()

        if token and bot_id:
            api_request_async(
                "GET",
                f"/chat/{bot_id}/history?limit=50",
                token=token,
                callback=self._on_history_loaded,
            )

    def _on_history_loaded(self, result):
        """Handle loaded chat history."""
        if result["success"] and result["data"]:
            items = result["data"].get("items", [])
            if items:
                # Clear welcome message
                self.messages_layout.clear_widgets()
                for item in items:
                    is_sent = item.get("direction") == "outgoing"
                    bubble = ChatBubble(
                        text=item.get("content", ""),
                        is_sent=is_sent,
                        timestamp=item.get("created_at", "")[:16],
                    )
                    self.messages_layout.add_widget(bubble)
                self._scroll_to_bottom()

    def _on_send(self, instance):
        """Send a message."""
        text = self.msg_input.text.strip()
        if not text:
            return

        # Add user message bubble
        from datetime import datetime
        now = datetime.now().strftime("%H:%M")
        user_bubble = ChatBubble(text=text, is_sent=True, timestamp=now)
        self.messages_layout.add_widget(user_bubble)
        self.msg_input.text = ""
        self._scroll_to_bottom()

        # Show typing indicator
        self.typing_box.opacity = 1

        # Send to API
        from apps.client.main import get_stored_token, get_stored_bot_id, api_request_async
        token = get_stored_token()
        bot_id = get_stored_bot_id()

        if token and bot_id:
            api_request_async(
                "POST",
                "/chat/send",
                data={"bot_id": bot_id, "to": "test", "content": text},
                token=token,
                callback=self._on_message_sent,
            )
        else:
            # Simulate response
            Clock.schedule_once(lambda dt: self._add_bot_response("Recebi sua mensagem! 🌸"), 1.5)

    def _on_message_sent(self, result):
        """Handle sent message response."""
        Clock.schedule_once(lambda dt: self._process_response(result), 0.5)

    def _process_response(self, result):
        """Process the API response."""
        self.typing_box.opacity = 0

        from datetime import datetime
        now = datetime.now().strftime("%H:%M")

        if result["success"]:
            reply = result["data"].get("reply", "Desculpa, nao entendi 😅")
        else:
            reply = "Erro ao enviar mensagem. Tente novamente."

        self._add_bot_response(reply, now)

    def _add_bot_response(self, text: str, timestamp: str = ""):
        """Add a bot response bubble."""
        from datetime import datetime
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")

        bot_bubble = ChatBubble(text=text, is_sent=False, timestamp=timestamp)
        self.messages_layout.add_widget(bot_bubble)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """Scroll to the bottom of the chat."""
        def _do_scroll(dt):
            self.scroll.scroll_y = 0
        Clock.schedule_once(_do_scroll, 0.1)

    def _on_back(self, instance):
        self.manager.current = "dashboard"
