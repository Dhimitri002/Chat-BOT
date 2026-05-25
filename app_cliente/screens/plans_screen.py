"""Plans Screen — Tela de planos e precos."""
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView


class PlansScreen(MDScreen):
    """Tela de planos disponiveis."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "plans"
        self.plans_data = [
            {
                "id": "free",
                "name": "Gratuito",
                "price": "R$ 0/mes",
                "features": [
                    "1 bot",
                    "100 mensagens/mes",
                    "Suporte basico",
                    "Sem custos",
                ],
                "is_popular": False,
                "is_current": False,
            },
            {
                "id": "starter",
                "name": "Starter",
                "price": "R$ 49/mes",
                "features": [
                    "3 bots",
                    "1.000 mensagens/mes",
                    "Suporte prioritario",
                    "Analytics basico",
                    "temas personalizados",
                ],
                "is_popular": False,
                "is_current": False,
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": "R$ 99/mes",
                "features": [
                    "10 bots",
                    "10.000 mensagens/mes",
                    "Suporte 24/7",
                    "Analytics avancado",
                    "API access",
                    "Multi-usuarios",
                ],
                "is_popular": True,
                "is_current": False,
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": "R$ 299/mes",
                "features": [
                    "Bots ilimitados",
                    "Mensagens ilimitadas",
                    "Suporte dedicado",
                    "SLA 99.9%",
                    "White label",
                    "Treinamento incluso",
                    "Gerente de conta",
                ],
                "is_popular": False,
                "is_current": False,
            },
        ]
        self.build()

    def build(self):
        from app_cliente.main import ThemeColors

        root = MDBoxLayout(
            orientation="vertical",
            md_bg_color=get_color_from_hex(ThemeColors.PRIMARY),
        )
        self.add_widget(root)

        # ---- Top Bar ----
        top_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=dp(12),
            spacing=dp(8),
            md_bg_color=get_color_from_hex(ThemeColors.SECONDARY),
        )

        back_btn = MDFlatButton(
            text="←",
            font_size="24sp",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_x=None,
            width=dp(48),
        )
        back_btn.bind(on_release=self._go_back)
        top_bar.add_widget(back_btn)

        top_bar.add_widget(MDLabel(
            text="⭐ Nossos Planos",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            bold=True,
        ))
        root.add_widget(top_bar)

        # ---- Content ----
        scroll = MDScrollView()
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=dp(16),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))
        scroll.add_widget(content)
        root.add_widget(scroll)

        # Header text
        header_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None,
            height=dp(70),
        )
        header_box.add_widget(MDLabel(
            text="Encontre o plano perfeito para voce!",
            font_style="H5",
            halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(32),
            bold=True,
        ))
        header_box.add_widget(MDLabel(
            text="Comece gratuito e escale conforme crescer",
            font_style="Body2",
            halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
            size_hint_y=None,
            height=dp(20),
        ))
        content.add_widget(header_box)

        # Current plan indicator
        self.current_plan_label = MDLabel(
            text="Plano atual: Gratuito",
            font_style="Subtitle1",
            halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(24),
            bold=True,
        )
        content.add_widget(self.current_plan_label)

        # Plan cards
        for plan in self.plans_data:
            plan_card = self._create_plan_card(plan)
            content.add_widget(plan_card)

        # ---- Comparison Table ----
        comparison_title = MDLabel(
            text="Comparacao de Recursos",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        )
        content.add_widget(comparison_title)

        table_card = MDCard(
            orientation="vertical",
            spacing=dp(4),
            padding=dp(16),
            radius=[16],
            elevation=2,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
        }
        table_card.bind(minimum_height=table_card.setter("height"))

        comparison_data = [
            ("Bots", "1", "3", "10", "ilimitados"),
            ("Mensagens/mes", "100", "1.000", "10.000", "ilimitadas"),
            ("Suporte", "Basico", "Prioritario", "24/7", "Dedicado"),
            ("Analytics", "Nao", "Sim", "Avancado", "Avancado"),
            ("API", "Nao", "Nao", "Sim", "Sim"),
            ("White Label", "Nao", "Nao", "Nao", "Sim"),
        ]

        for feature, free, starter, pro, enterprise in comparison_data:
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(28),
                spacing=dp(4),
            )
            row.add_widget(MDLabel(
                text=feature,
                font_style="Body2",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
                size_hint_x=0.3,
                bold=True,
            ))
            row.add_widget(MDLabel(
                text=free, font_style="Caption", halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
                size_hint_x=0.175,
            ))
            row.add_widget(MDLabel(
                text=starter, font_style="Caption", halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
                size_hint_x=0.175,
            ))
            row.add_widget(MDLabel(
                text=pro, font_style="Caption", halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
                size_hint_x=0.175,
            ))
            row.add_widget(MDLabel(
                text=enterprise, font_style="Caption", halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.SUCCESS),
                size_hint_x=0.175,
            ))
            table_card.add_widget(row)

        content.add_widget(table_card)

        # Footer
        footer_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(80),
        )

        flora_btn = MDRaisedButton(
            text="🌸 Falar com Flora para escolher",
            md_bg_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            pos_hint={"center_x": 0.5},
            radius=[12],
        )
        flora_btn.bind(on_release=self._go_to_flora)
        footer_box.add_widget(flora_btn)

        footer_box.add_widget(MDLabel(
            text="Todos os planos incluem atualizacoes gratuitas",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
            size_hint_y=None,
            height=dp(16),
        ))

        content.add_widget(footer_box)
        content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(20)))

    def _create_plan_card(self, plan):
        """Cria um cartao de plano customizado."""
        from app_cliente.main import ThemeColors

        is_current = plan.get("is_current", False)
        is_popular = plan.get("is_popular", False)
        border_color = ThemeColors.HIGHLIGHT if is_popular else (
            ThemeColors.SUCCESS if is_current else ThemeColors.CARD
        )
        bg_color = ThemeColors.ACCENT if (is_current or is_popular) else ThemeColors.CARD

        card = MDCard(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(20),
            radius=[20],
            elevation=6 if (is_current or is_popular) else 2,
            md_bg_color=get_color_from_hex(bg_color),
            size_hint_y=None,
        )
        card.bind(minimum_height=card.setter("height"))

        # Header row
        header_row = MDBoxLayout(
            size_hint_y=None,
            height=dp(32),
            spacing=dp(8),
        )
        header_row.add_widget(MDLabel(
            text=plan["name"],
            font_style="H5",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            bold=True,
        ))

        if is_popular:
            header_row.add_widget(MDLabel(
                text="Mais Popular",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.WARNING),
                bold=True,
            ))
        elif is_current:
            header_row.add_widget(MDLabel(
                text="Seu Plano Atual",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.SUCCESS),
                bold=True,
            ))
        else:
            header_row.add_widget(MDLabel(text=""))

        card.add_widget(header_row)

        # Price
        card.add_widget(MDLabel(
            text=plan["price"],
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(28),
        ))

        # Divider
        card.add_widget(MDBoxLayout(
            size_hint_y=None,
            height=dp(1),
            md_bg_color=get_color_from_hex(ThemeColors.DIVIDER),
        ))

        # Features
        for feat in plan["features"]:
            feat_box = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(26),
                spacing=dp(8),
            )
            feat_box.add_widget(MDLabel(
                text="OK",
                font_style="Body2",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.SUCCESS),
                size_hint_x=None,
                width=dp(28),
                bold=True,
            ))
            feat_box.add_widget(MDLabel(
                text=feat,
                font_style="Body2",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
            ))
            card.add_widget(feat_box)

        # Button
        btn = MDRaisedButton(
            text="✓ Plano Atual" if is_current else "Escolher Plano",
            md_bg_color=get_color_from_hex(
                ThemeColors.SUCCESS if is_current else ThemeColors.HIGHLIGHT
            ),
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            pos_hint={"center_x": 0.5},
            disabled=is_current,
            size_hint_y=None,
            height=dp(44),
            radius=[12],
        )
        if not is_current:
            btn.bind(on_release=lambda inst, p=plan: self._select_plan(p))
        card.add_widget(btn)

        return card

    def _select_plan(self, plan):
        """Processo de selecao de assinatura de plano."""
        self.current_plan_label.text = f"Plano: {plan['name']} selecionado!"
        self.current_plan_label.text_color = get_color_from_hex("#4ecca3")

        # Update plans_data to show selection
        for p in self.plans_data:
            p["is_current"] = (p["id"] == plan["id"])

        # In a real app, this would trigger payment flow
        # For now, just show a message. In production, replace with:
        #   threading.Thread(target=lambda: api.subscribe_plan(plan["id"]), daemon=True).start()

    def _go_to_flora(self, *args):
        self.manager.transition.direction = "left"
        self.manager.current = "flora_chat"

    def _go_back(self, *args):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_enter(self):
        app = self.manager.parent
        if app and app.user_plan:
            self.current_plan_label.text = f"Plano atual: {app.user_plan}"
            for p in self.plans_data:
                p["is_current"] = (p["name"] == app.user_plan)
