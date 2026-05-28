# ═══════════════════════════════════════════════════════════════
# Flora Platform — Intents Screen
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
from kivymd.uix.switch import MDSwitch, MDSwitchThumb
from kivymd.uix.divider import MDDivider
from kivymd.uix.chip import MDChip, MDChipText


class IntentsScreen(MDScreen):
    """List and manage bot intents (auto-reply patterns)."""

    def __self__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
            text="Intencoes 🎯",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        ))
        add_btn = MDIconButton(
            icon="plus",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            on_release=self._on_add,
        )
        top_bar.add_widget(add_btn)
        layout.add_widget(top_bar)

        # Content
        scroll = MDScrollView(
            pos_hint={"top": 0.92},
            size_hint=(1, 0.92),
            do_scroll_x=False,
        )

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(16), dp(8), dp(16), dp(100)],
            size_hint_y=None,
            adaptive_height=True,
        )

        # Info card
        info_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(70),
            radius=[dp(14)],
            md_bg_color=(0.424, 0.388, 1.0, 0.1),
            padding=[dp(14), dp(10)],
        )
        info_card.add_widget(MDLabel(
            text="🎯 Intencoes sao padroes de resposta automatica. "
                 "Quando uma mensagem contem o gatilho, o bot responde automaticamente.",
            font_style="Label",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        ))
        content.add_widget(info_card)

        # Intent list
        self.intents_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
        )

        # Sample intents
        sample_intents = [
            {
                "name": "Saudacao",
                "trigger": "ola, oi, bom dia",
                "response": "Ola! 👋 Como posso te ajudar?",
                "count": 42,
                "enabled": True,
            },
            {
                "name": "Despedida",
                "trigger": "tchau, ate mais, falou",
                "response": "Ate mais! 👋 Volte sempre!",
                "count": 18,
                "enabled": True,
            },
            {
                "name": "Preco",
                "trigger": "preco, valor, quanto custa",
                "response": "Nossos planos comecam em R$29/mes. Quer saber mais? 💰",
                "count": 31,
                "enabled": True,
            },
            {
                "name": "Suporte",
                "trigger": "ajuda, suporte, problema",
                "response": "Vou te conectar com nosso suporte! Um momento... 🛠️",
                "count": 12,
                "enabled": False,
            },
        ]

        for intent in sample_intents:
            card = self._create_intent_card(intent)
            self.intents_list.add_widget(card)

        content.add_widget(self.intents_list)
        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def _create_intent_card(self, intent: dict) -> MDCard:
        """Create an intent card."""
        card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(120),
            radius=[dp(16)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(16), dp(12)],
            spacing=dp(4),
            elevation=2,
        )

        # Header row
        header = MDBoxLayout(
            size_hint=(1, None),
            height=dp(28),
            spacing=dp(8),
        )
        header.add_widget(MDLabel(
            text=f"🎯 {intent['name']}",
            font_style="Title",
            role="small",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_x=0.6,
        ))

        # Enable/disable switch
        switch = MDSwitch(
            active=intent.get("enabled", True),
            pos_hint={"center_y": 0.5},
            thumb_color_active=(0.424, 0.388, 1.0, 1),
            thumb_color_inactive=(0.4, 0.4, 0.45, 1),
            track_color_active=(0.424, 0.388, 1.0, 0.3),
            track_color_inactive=(0.2, 0.2, 0.3, 1),
        )
        header.add_widget(switch)
        card.add_widget(header)

        # Trigger
        card.add_widget(MDLabel(
            text=f"Gatilho: {intent['trigger']}",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
        ))

        # Response preview
        card.add_widget(MDLabel(
            text=f"Resposta: {intent['response'][:50]}...",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        ))

        # Footer with count and actions
        footer = MDBoxLayout(
            size_hint=(1, None),
            height=dp(24),
            spacing=dp(4),
        )
        footer.add_widget(MDLabel(
            text=f"Usado {intent['count']}x",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 0.55, 1),
            size_hint_x=0.5,
        ))

        edit_btn = MDButton(
            MDButtonText(text="Editar", theme_text_color="Custom", text_color=(0.424, 0.388, 1.0, 1)),
            style="text",
            size_hint_x=0.25,
        )
        footer.add_widget(edit_btn)

        del_btn = MDButton(
            MDButtonText(text="Excluir", theme_text_color="Custom", text_color=(0.957, 0.263, 0.212, 1)),
            style="text",
            size_hint_x=0.25,
        )
        footer.add_widget(del_btn)

        card.add_widget(footer)
        return card

    def _on_add(self, instance):
        """Add a new intent."""
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            if app and hasattr(app, 'show_snackbar'):
                app.show_snackbar("Formulario de nova intencao em breve!", (0.424, 0.388, 1.0, 1))
        except Exception:
            pass

    def _on_back(self, instance):
        self.manager.current = "dashboard"
