"""
Flora Admin — Tela de Planos
=============================
Gerenciamento dos planos de assinatura da plataforma.
Criação, edição, ativação e métricas por plano.
"""

from kivy.clock import Clock
from kivy.metrics import dp

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFloatingActionButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.textfield import MDTextField
from apps.shared.theme import FloraColors, FloraTheme


class PlansScreen(MDScreen):
    """Tela de gerenciamento de planos de assinatura."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self._build_ui()

    def _build_ui(self):
        c = FloraColors()
        layout = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8))

        # Header
        header = MDBoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        title = MDLabel(
            text="💎  Planos",
            font_style="H4",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
            bold=True,
        )
        header.add_widget(title)
        layout.add_widget(header)

        # Plan cards
        self.content = MDBoxLayout(orientation="vertical", spacing=dp(12))
        layout.add_widget(self.content)

        # FAB
        fab = MDFloatingActionButton(
            icon="plus",
            theme_icon_color="Custom",
            icon_color=c.to_rgba(c.WHITE),
            md_bg_color=c.to_rgba(c.PRIMARY_PURPLE),
            pos_hint={"center_x": 0.92, "center_y": 0.08},
            on_release=self._show_create_dialog,
        )
        layout.add_widget(fab)
        self.add_widget(layout)

    def on_enter(self):
        Clock.schedule_once(lambda dt: self._load_plans(), 0.3)

    def _load_plans(self):
        """Carrega planos existentes."""
        self.content.clear_widgets()
        c = FloraColors()

        plans = [
            {
                "name": "Gratuito",
                "price": "R$ 0",
                "bots": "1 bot",
                "messages": "100 msg/mês",
                "users": "12 usuários",
                "color": c.INFO,
            },
            {
                "name": "Starter",
                "price": "R$ 49/mês",
                "bots": "3 bots",
                "messages": "5.000 msg/mês",
                "users": "45 usuários",
                "color": c.PRIMARY_PURPLE,
            },
            {
                "name": "Pro",
                "price": "R$ 99/mês",
                "bots": "10 bots",
                "messages": "25.000 msg/mês",
                "users": "120 usuários",
                "color": c.ACCENT_PINK,
            },
            {
                "name": "Enterprise",
                "price": "R$ 299/mês",
                "bots": "Ilimitados",
                "messages": "Ilimitadas",
                "users": "500+ usuários",
                "color": c.WARNING,
            },
        ]

        for plan in plans:
            card = MDCard(
                orientation="vertical",
                padding=dp(16),
                spacing=dp(8),
                size_hint_y=None,
                height=dp(160),
                radius=[FloraTheme.CARD_RADIUS],
                elevation=FloraTheme.CARD_ELEVATION,
                md_bg_color=c.to_rgba(c.SURFACE_CARD),
            )

            # Plan header
            top = MDBoxLayout(size_hint_y=None, height=dp(40)
            )
            name_lbl = MDLabel(
                text=f"[b]{plan['name']}[/b]",
                font_style="H5",
                theme_text_color="Custom",
                text_color=c.to_rgba(plan["color"]),
                bold=True,
                markup=True,
            )
            top.add_widget(name_lbl)
            price_lbl = MDLabel(
                text=f"[b]{plan['price']}[/b]",
                font_style="H5",
                theme_text_color="Custom",
                text_color=c.to_rgba(c.TEXT_PRIMARY),
                bold=True,
                markup=True,
                halign="right",
            )
            top.add_widget(price_lbl)
            card.add_widget(top)

            # Features
            features = MDBoxLayout(orientation="vertical", spacing=dp(2))
            features.add_widget(MDLabel(
                text=f"🤖 {plan['bots']}  |  💬 {plan['messages']}  |  👥 {plan['users']}",
                theme_text_color="Custom",
                text_color=c.to_rgba(c.TEXT_SECONDARY),
                font_style="Body",
            ))
            card.add_widget(features)

            # Spacer
            card.add_widget(MDBoxLayout())

            # Actions
            actions = MDBoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
            edit_btn = MDIconButton(icon="pencil", theme_icon_color="Custom",
                                    icon_color=c.to_rgba(c.ACCENT_PINK),
                                    on_release=lambda inst, p=plan: self._edit_plan(p))
            delete_btn = MDIconButton(icon="delete", theme_icon_color="Custom",
                                      icon_color=c.to_rgba(c.ERROR))
            actions.add_widget(edit_btn)
            actions.add_widget(delete_btn)
            card.add_widget(actions)

            self.content.add_widget(card)

    def _edit_plan(self, plan):
        MDSnackbar(MDSnackbarText(text=f"Editando plano: {plan['name']}")).open()

    def _show_create_dialog(self, instance):
        c = FloraColors()
        content = MDBoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, height=dp(250))
        content.add_widget(MDTextField(hint_text="Nome do plano", mode="rectangle",
                                       radius=[FloraTheme.INPUT_RADIUS]))
        content.add_widget(MDTextField(hint_text="Preço (R$)", mode="rectangle",
                                       radius=[FloraTheme.INPUT_RADIUS]))
        content.add_widget(MDTextField(hint_text="Limite de bots", mode="rectangle",
                                       radius=[FloraTheme.INPUT_RADIUS]))
        content.add_widget(MDTextField(hint_text="Limite de mensagens/mês", mode="rectangle",
                                       radius=[FloraTheme.INPUT_RADIUS]))

        self.dialog = MDDialog(
            title="Novo Plano",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", theme_text_color="Custom",
                             text_color=c.to_rgba(c.TEXT_SECONDARY)),
                MDFillRoundFlatButton(text="Criar", md_bg_color=c.to_rgba(c.PRIMARY_PURPLE),
                                      on_release=self._create_plan),
            ],
        )
        self.dialog.open()

    def _create_plan(self, instance):
        self.dialog.dismiss()
        MDSnackbar(MDSnackbarText(text="Plano criado com sucesso!")).open()
