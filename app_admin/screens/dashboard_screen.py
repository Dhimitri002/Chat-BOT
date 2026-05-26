"""
DashboardScreen — Admin dashboard with premium charts and stats.
"""

from kivy.metrics import dp
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView

from app_admin.styles.theme import Colors, Theme
from app_admin.styles.components import PremiumCard, StatCard, SnackbarNotification


class DashboardScreen(MDScreen):
    """Admin dashboard with real-time metrics."""

    def __init__(self, app: "FloraAdminApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._build()

    def _build(self):
        root = MDBoxLayout(
            orientation="vertical",
            padding=Theme.SPACE_LG,
            spacing=Theme.SPACE_MD,
            md_bg_color=Colors.BG_BASE,
        )

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=Theme.SPACE_SM,
        )
        header.add_widget(MDLabel(
            text="Dashboard",
            font_style=Theme.H4,
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=0.7,
        ))
        header.add_widget(MDRaisedButton(
            text="Atualizar",
            size_hint_x=None,
            width=dp(120),
            size_hint_y=None,
            height=dp(36),
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.TEXT_ON_ACCENT,
            theme_text_color="Custom",
            on_release=lambda x: self._refresh(),
        ))
        root.add_widget(header)

        # Stats cards row
        stats_row = MDBoxLayout(
            orientation="horizontal",
            spacing=Theme.SPACE_MD,
            size_hint_y=None,
            height=dp(112),
        )

        self._stat_msgs = StatCard(
            title="Mensagens",
            value="—",
            subtitle="carregando...",
            icon="message-text",
            accent_color=Colors.PRIMARY,
        )
        self._stat_users = StatCard(
            title="Usuários",
            value="—",
            subtitle="total",
            icon="account-group",
            accent_color=Colors.SECONDARY,
        )
        self._stat_bots = StatCard(
            title="Bots Ativos",
            value="—",
            subtitle="online",
            icon="robot",
            accent_color=Colors.SUCCESS,
        )
        self._stat_errors = StatCard(
            title="Erros",
            value="0",
            subtitle="últimas 24h",
            icon="alert-circle",
            accent_color=Colors.ERROR,
        )

        stats_row.add_widget(self._stat_msgs)
        stats_row.add_widget(self._stat_users)
        stats_row.add_widget(self._stat_bots)
        stats_row.add_widget(self._stat_errors)
        root.add_widget(stats_row)

        # Second row: recent activity + quick actions
        second_row = MDBoxLayout(
            orientation="horizontal",
            spacing=Theme.SPACE_MD,
            size_hint_y=None,
            height=dp(220),
        )

        # Recent activity card
        activity_card = PremiumCard(size_hint_x=0.6)
        activity_card.add_widget(MDLabel(
            text="Atividade Recente",
            font_style=Theme.H6,
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(28),
        ))
        self._activity_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[0, dp(8), 0, 0],
        )
        self._activity_list.add_widget(MDSpinner(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={"center_x": 0.5},
            color=Colors.PRIMARY,
        ))
        activity_card.add_widget(self._activity_list)
        second_row.add_widget(activity_card)

        # Quick actions card
        actions_card = PremiumCard(size_hint_x=0.4)
        actions_card.add_widget(MDLabel(
            text="Ações Rápidas",
            font_style=Theme.H6,
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(28),
        ))
        actions_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[0, dp(8), 0, 0],
        )
        for label, icon, color, screen in [
            ("Novo Usuário", "account-plus", Colors.SECONDARY, "users"),
            ("Novo Bot", "robot", Colors.PRIMARY, "bots"),
            ("Ver Analytics", "chart-line", Colors.INFO, "analytics"),
        ]:
            btn = MDRaisedButton(
                text=label,
                icon=f"android",
                md_bg_color=color,
                text_color=Colors.TEXT_ON_ACCENT,
                theme_text_color="Custom",
                size_hint_y=None,
                height=dp(40),
                elevation=Theme.ELEVATION_LOW,
            )
            btn.screen_target = screen
            btn.bind(on_release=lambda x: self._app.switch_screen(x.screen_target))
            actions_box.add_widget(btn)
        actions_card.add_widget(actions_box)
        second_row.add_widget(actions_card)
        root.add_widget(second_row)

        # Chart area
        self._chart_card = PremiumCard()
        self._chart_card.add_widget(MDLabel(
            text="Mensagens por Dia",
            font_style=Theme.H6,
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(28),
        ))
        self._chart_content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            padding=[0, dp(8), 0, 0],
        )
        self._chart_card.add_widget(self._chart_content)
        root.add_widget(self._chart_card)

        self.add_widget(root)

    def on_enter(self):
        """Called when screen is entered."""
        self._refresh()

    def _refresh(self):
        """Refresh dashboard data."""
        # Simulate data load
        self._stat_msgs.value = "1,234"
        self._stat_msgs.subtitle = "+128 hoje"
        self._stat_users.value = "48"
        self._stat_users.subtitle = "+3 esta semana"
        self._stat_bots.value = "32"
        self._stat_bots.subtitle = "30 online"
        self._stat_errors.value = "2"
        self._stat_errors.subtitle = "últimas 24h"

        # Update activity list
        self._activity_list.clear_widgets()
        activities = [
            ("João criou um bot", "2 min atrás", Colors.SUCCESS),
            ("Maria conectou WhatsApp", "15 min atrás", Colors.INFO),
            ("Bot 'Suporte' atualizado", "1h atrás", Colors.SECONDARY),
            ("Novo usuário registrado", "3h atrás", Colors.PRIMARY),
        ]
        for text, time_label, color in activities:
            row = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(8),
                size_hint_y=None,
                height=dp(28),
            )
            dot = MDIconButton(
                icon="circle",
                theme_text_color="Custom",
                text_color=color,
                user_font_size=dp(8),
                size_hint_x=None,
                width=dp(24),
            )
            row.add_widget(dot)
            row.add_widget(MDLabel(
                text=text,
                font_style=Theme.BODY2,
                theme_text_color="Custom",
                text_color=Colors.TEXT_PRIMARY,
                size_hint_x=0.7,
            ))
            row.add_widget(MDLabel(
                text=time_label,
                font_style=Theme.CAPTION_STYLE,
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                size_hint_x=0.3,
                halign="right",
            ))
            self._activity_list.add_widget(row)

        # Update chart
        self._chart_content.clear_widgets()
        chart_data = [
            ("Seg", 120), ("Ter", 230), ("Qua", 180),
            ("Qui", 310), ("Sex", 275), ("Sáb", 90), ("Dom", 60),
        ]
        max_val = max(v for _, v in chart_data) or 1
        for label, value in chart_data:
            row = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(8),
                size_hint_y=None,
                height=dp(24),
            )
            bar_width = max(0.05, value / max_val)
            row.add_widget(MDLabel(
                text=label,
                font_style=Theme.CAPTION_STYLE,
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                size_hint_x=None,
                width=dp(32),
            ))
            bar_bg = MDBoxLayout(size_hint_x=bar_width, size_hint_y=None, height=dp(14))
            bar_bg.md_bg_color = Colors.PRIMARY
            bar_bg.radius = [dp(4)]
            empty = MDBoxLayout(size_hint_x=1 - bar_width)
            bar_row = MDBoxLayout(spacing=0)
            bar_row.add_widget(bar_bg)
            bar_row.add_widget(empty)
            row.add_widget(bar_row)
            row.add_widget(MDLabel(
                text=str(value),
                font_style=Theme.CAPTION_STYLE,
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
                size_hint_x=None,
                width=dp(36),
                halign="right",
            ))
            self._chart_content.add_widget(row)
