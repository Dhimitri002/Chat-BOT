# ═══════════════════════════════════════════════════════════════
# Flora Platform — Plans Screen
# ═══════════════════════════════════════════════════════════════

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.chip import MDChip, MDChipText


class PlansScreen(MDScreen):
    """Show current plan and available plans with pricing."""

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
            text="Planos 💰",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        ))
        layout.add_widget(top_bar)

        # Content
        scroll = MDScrollView(
            pos_hint={"top": 0.92},
            size_hint=(1, 0.92),
            do_scroll_x=False,
        )

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=[dp(16), dp(8), dp(16), dp(100)],
            size_hint_y=None,
            adaptive_height=True,
        )

        # Current plan card
        current_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(100),
            radius=[dp(20)],
            md_bg_color=(0.424, 0.388, 1.0, 0.15),
            padding=[dp(20), dp(16)],
            spacing=dp(4),
            elevation=4,
        )
        current_card.add_widget(MDLabel(
            text="Plano Atual",
            font_style="Label",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        ))
        current_card.add_widget(MDLabel(
            text="Basico 🌱",
            font_style="Headline",
            role="small",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
        ))
        current_card.add_widget(MDLabel(
            text="R$ 29,00/mes • 100 msgs/dia • 1 bot",
            font_style="Body",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        ))
        content.add_widget(current_card)

        # Section title
        content.add_widget(MDLabel(
            text="Todos os Planos",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(32),
        ))

        # Plans
        plans = [
            {
                "name": "Gratuito",
                "emoji": "🌱",
                "price_monthly": "R$ 0",
                "price_yearly": "R$ 0",
                "features": ["1 bot", "50 msgs/dia", "100 contatos", "Suporte basico"],
                "highlighted": False,
                "badge": None,
            },
            {
                "name": "Basico",
                "emoji": "🌿",
                "price_monthly": "R$ 29",
                "price_yearly": "R$ 290",
                "features": ["1 bot", "500 msgs/dia", "1.000 contatos", "Suporte por email", "Intents basicos"],
                "highlighted": True,
                "badge": "Plano Atual",
            },
            {
                "name": "Pro",
                "emoji": "🌳",
                "price_monthly": "R$ 59",
                "price_yearly": "R$ 590",
                "features": ["3 bots", "2.000 msgs/dia", "5.000 contatos", "Suporte prioritario", "Flora AI", "Comandos personalizados"],
                "highlighted": False,
                "badge": "Popular",
            },
            {
                "name": "Enterprise",
                "emoji": "🏢",
                "price_monthly": "R$ 149",
                "price_yearly": "R$ 1.490",
                "features": ["Bots ilimitados", "Msgs ilimitadas", "Contatos ilimitados", "Suporte 24/7", "Flora AI Pro", "API access", "Webhooks"],
                "highlighted": False,
                "badge": None,
            },
        ]

        for plan in plans:
            card = self._create_plan_card(plan)
            content.add_widget(card)

        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def _create_plan_card(self, plan: dict) -> MDCard:
        """Create a pricing plan card."""
        is_highlighted = plan.get("highlighted", False)

        card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(200),
            radius=[dp(20)],
            md_bg_color=(0.424, 0.388, 1.0, 0.15) if is_highlighted else (0.13, 0.16, 0.28, 1),
            padding=[dp(20), dp(16)],
            spacing=dp(6),
            elevation=6 if is_highlighted else 2,
        )

        # Header
        header = MDBoxLayout(
            size_hint=(1, None),
            height=dp(36),
            spacing=dp(8),
        )
        header.add_widget(MDLabel(
            text=f"{plan['emoji']} {plan['name']}",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_x=0.6,
        ))

        if plan.get("badge"):
            badge = MDChip(
                MDChipText(
                    text=plan["badge"],
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                ),
                md_bg_color=(0.424, 0.388, 1.0, 1) if is_highlighted else (1.0, 0.420, 0.616, 1),
            )
            header.add_widget(badge)

        card.add_widget(header)

        # Price
        price_box = MDBoxLayout(
            size_hint=(1, None),
            height=dp(36),
            spacing=dp(4),
        )
        price_box.add_widget(MDLabel(
            text=plan["price_monthly"],
            font_style="Headline",
            role="small",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
        ))
        price_box.add_widget(MDLabel(
            text="/mes",
            font_style="Body",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
            pos_hint={"center_y": 0.3},
        ))
        card.add_widget(price_box)

        # Yearly price
        card.add_widget(MDLabel(
            text=f"ou {plan['price_yearly']}/ano (economize 17%)",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 0.55, 1),
        ))

        # Features
        features_text = "  •  ".join(plan["features"][:4])
        card.add_widget(MDLabel(
            text=features_text,
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        ))

        # Action button
        if is_highlighted:
            btn = MDButton(
                MDButtonText(text="Plano Atual ✓"),
                style="filled",
                size_hint=(1, None),
                height=dp(40),
                md_bg_color=(0.424, 0.388, 1.0, 0.3),
                disabled=True,
            )
        else:
            btn = MDButton(
                MDButtonText(text="Fazer Upgrade" if plan["name"] != "Gratuito" else "Comecar Gratis"),
                style="filled",
                size_hint=(1, None),
                height=dp(40),
                md_bg_color=(0.424, 0.388, 1.0, 1),
                on_release=lambda x, p=plan: self._on_upgrade(p),
            )
        card.add_widget(btn)

        return card

    def _on_upgrade(self, plan: dict):
        """Handle plan upgrade."""
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            if app and hasattr(app, 'show_snackbar'):
                app.show_snackbar(f"Upgrade para {plan['name']} em breve!", (0.424, 0.388, 1.0, 1))
        except Exception:
            pass

    def _on_back(self, instance):
        self.manager.current = "dashboard"
