# ═══════════════════════════════════════════════════════════════
# Flora Platform — Flora Chat Screen
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
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.progressindicator import MDCircularProgressIndicator


class FloraChatBubble(MDCard):
    """A chat message bubble for Flora chat."""

    def __init__(self, text: str, is_flora: bool, timestamp: str = "", **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(None, None),
            radius=[dp(16)],
            padding=[dp(12), dp(8)],
            elevation=1,
            **kwargs,
        )

        if is_flora:
            self.md_bg_color = (0.2, 0.23, 0.35, 1)
            self.pos_hint = {"x": 0.05}
            self.size_hint_x = 0.78
        else:
            self.md_bg_color = (0.424, 0.388, 1.0, 1)
            self.pos_hint = {"right": 0.95}
            self.size_hint_x = 0.78

        # Avatar + text layout
        content_box = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
        )

        if is_flora:
            avatar = MDLabel(
                text="🌸",
                font_size=sp(20),
                size_hint=(None, None),
                size=(dp(28), dp(28)),
            )
            content_box.add_widget(avatar)

        msg_label = MDLabel(
            text=text,
            font_style="Body",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            adaptive_height=True,
            text_size=(dp(220), None),
        )
        msg_label.bind(texture_size=lambda *x: msg_label.setter('height')(msg_label, msg_label.texture_size[1]))
        content_box.add_widget(msg_label)
        content_box.bind(minimum_height=content_box.setter('height'))

        self.add_widget(content_box)

        # Timestamp
        if timestamp:
            time_label = MDLabel(
                text=timestamp,
                font_style="Label",
                role="small",
                halign="right" if not is_flora else "left",
                theme_text_color="Custom",
                text_color=(0.5, 0.5, 0.55, 0.7),
                size_hint_y=None,
                height=dp(14),
            )
            self.add_widget(time_label)

        self.bind(minimum_height=self.setter('height'))


class FloraChatScreen(MDScreen):
    """Chat with Flora AI assistant."""

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

        # Flora avatar in top bar
        top_bar.add_widget(MDLabel(
            text="🌸",
            font_size=sp(20),
            size_hint=(None, None),
            size=(dp(32), dp(32)),
        ))
        top_bar.add_widget(MDLabel(
            text="Flora AI",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        ))

        # Online indicator
        top_bar.add_widget(MDBoxLayout(
            size_hint=(None, None),
            size=(dp(8), dp(8)),
            md_bg_color=(0.298, 0.686, 0.314, 1),
            radius=[dp(4)],
        ))
        top_bar.add_widget(MDLabel(
            text="Online",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.298, 0.686, 0.314, 1),
        ))

        layout.add_widget(top_bar)

        # Quick action chips
        chips_scroll = MDScrollView(
            pos_hint={"top": 0.92},
            size_hint=(1, None),
            height=dp(48),
            do_scroll_y=False,
            bar_width=0,
        )
        chips_box = MDBoxLayout(
            spacing=dp(8),
            padding=[dp(12), dp(4)],
            size_hint_x=None,
            adaptive_width=True,
        )

        quick_actions = [
            "Como conectar o WhatsApp?",
            "Como funciona a licenca?",
            "Ver meus planos",
            "Configurar meu bot",
        ]

        for action in quick_actions:
            chip = MDChip(
                MDChipText(
                    text=action,
                    theme_text_color="Custom",
                    text_color=(0.7, 0.7, 0.75, 1),
                ),
                md_bg_color=(0.13, 0.16, 0.28, 1),
                on_release=lambda x, a=action: self._on_quick_action(a),
            )
            chips_box.add_widget(chip)

        chips_scroll.add_widget(chips_box)
        layout.add_widget(chips_scroll)

        # Messages area
        self.scroll = MDScrollView(
            pos_hint={"top": 0.84},
            size_hint=(1, 0.74),
            do_scroll_x=False,
            bar_width=dp(4),
            bar_color=(0.424, 0.388, 1.0, 0.3),
        )

        self.messages_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(12), dp(8), dp(12), dp(80)],
            size_hint_y=None,
            adaptive_height=True,
        )

        # Welcome message from Flora
        welcome = FloraChatBubble(
            text="Ola! 🌸 Sou a Flora, sua assistente inteligente! "
                 "Posso te ajudar a configurar seu bot, conectar o WhatsApp, "
                 "entender seus planos e muito mais. Como posso te ajudar hoje?",
            is_flora=True,
        )
        self.messages_layout.add_widget(welcome)

        self.scroll.add_widget(self.messages_layout)
        layout.add_widget(self.scroll)

        # Typing indicator
        self.typing_box = MDBoxLayout(
            size_hint=(1, None),
            height=dp(36),
            pos_hint={"y": 0.1},
            padding=[dp(16), 0],
            opacity=0,
        )
        typing_card = MDCard(
            size_hint=(None, None),
            size=(dp(90), dp(30)),
            radius=[dp(15)],
            md_bg_color=(0.2, 0.23, 0.35, 1),
            padding=[dp(12), dp(4)],
        )
        typing_content = MDBoxLayout(spacing=dp(2))
        typing_content.add_widget(MDLabel(text="🌸", font_size=sp(14), size_hint_x=0.3))
        typing_content.add_widget(MDLabel(
            text="digitando...",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
            size_hint_x=0.7,
        ))
        typing_card.add_widget(typing_content)
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
            hint_text="Pergunte a Flora...",
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

    def _on_quick_action(self, action: str):
        """Handle quick action chip tap."""
        self.msg_input.text = action
        self._on_send(None)

    def _on_send(self, instance):
        """Send a message to Flora AI."""
        text = self.msg_input.text.strip()
        if not text:
            return

        # Add user message
        from datetime import datetime
        now = datetime.now().strftime("%H:%M")
        user_bubble = FloraChatBubble(text=text, is_flora=False, timestamp=now)
        self.messages_layout.add_widget(user_bubble)
        self.msg_input.text = ""
        self._scroll_to_bottom()

        # Show typing
        self.typing_box.opacity = 1

        # Send to Flora API
        from apps.client.main import get_stored_token, api_request_async
        token = get_stored_token()

        if token:
            api_request_async(
                "POST",
                "/flora/chat",
                data={"message": text},
                token=token,
                callback=self._on_flora_response,
            )
        else:
            Clock.schedule_once(lambda dt: self._add_flora_response(
                "Ola! 🌸 Para conversar comigo, voce precisa estar logada. "
                "Va para a tela de licenca para comecar!"
            ), 1.5)

    def _on_flora_response(self, result):
        """Handle Flora AI response."""
        Clock.schedule_once(lambda dt: self._process_flora_response(result), 0.5)

    def _process_flora_response(self, result):
        """Process Flora's response."""
        self.typing_box.opacity = 0

        from datetime import datetime
        now = datetime.now().strftime("%H:%M")

        if result["success"]:
            data = result["data"]
            reply = data.get("response", "Desculpa, nao entendi. Pode repetir? 😅")
        else:
            reply = "Desculpa, estou com problemas tecnicos. Tente novamente em instantes. 🌸"

        self._add_flora_response(reply, now)

    def _add_flora_response(self, text: str, timestamp: str = ""):
        """Add a Flora response bubble."""
        from datetime import datetime
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")

        flora_bubble = FloraChatBubble(text=text, is_flora=True, timestamp=timestamp)
        self.messages_layout.add_widget(flora_bubble)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """Scroll to the bottom of the chat."""
        def _do_scroll(dt):
            self.scroll.scroll_y = 0
        Clock.schedule_once(_do_scroll, 0.1)

    def _on_back(self, instance):
        self.manager.current = "dashboard"
