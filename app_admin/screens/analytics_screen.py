"""
AnalyticsScreen — Admin analytics with charts and data tables.

Fetches from:
  - GET /api/v1/analytics/dashboard      (user-scoped)
  - GET /api/v1/analytics/llm-usage
"""

from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView

from app_admin.styles.theme import Colors, Theme


def _make_chart_card(title: str, data_pairs: list[tuple[str, int]], accent_color) -> MDCard:
    """Build a simple bar-chart card from (label, value) pairs."""
    card = MDCard(
        orientation="vertical",
        padding=Theme.SPACE_LG,
        spacing=Theme.SPACE_SM,
        md_bg_color=Colors.BG_CARD,
        radius=[Theme.RADIUS_LARGE],
        elevation=Theme.ELEVATION_LOW,
        size_hint_y=None,
    )

    card.add_widget(MDLabel(
        text=title,
        font_style="H6",
        bold=True,
        theme_text_color="Custom",
        text_color=Colors.TEXT_PRIMARY,
        size_hint_y=None,
        height=dp(32),
    ))

    if not data_pairs:
        card.add_widget(MDLabel(
            text="Sem dados.",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_y=None,
            height=dp(30),
        ))
        card.height = dp(100)
        return card

    max_val = max(v for _, v in data_pairs) if data_pairs else 1
    if max_val == 0:
        max_val = 1

    bars_container = MDBoxLayout(
        orientation="vertical",
        spacing=dp(4),
        size_hint_y=None,
    )
    for lbl, val in data_pairs:
        bar_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(28),
            spacing=dp(8),
        )
        bar_row.add_widget(MDLabel(
            text=lbl,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            size_hint_x=None,
            width=dp(80),
            shorten=True,
        ))

        # Bar background
        bar_bg = MDBoxLayout(
            size_hint_x=0.7,
            md_bg_color=(*Colors.BG_INPUT[:3], 1),
            radius=[dp(4)],
        )
        fill_ratio = val / max_val
        bar_fill = MDBoxLayout(
            size_hint_x=fill_ratio,
            md_bg_color=(*accent_color[:3], 0.7),
            radius=[dp(4)],
        )
        bar_bg.add_widget(bar_fill)
        bar_bg.add_widget(MDBoxLayout())  # spacer remaining
        bar_row.add_widget(bar_bg)

        bar_row.add_widget(MDLabel(
            text=str(val),
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=None,
            width=dp(40),
            halign="right",
        ))
        bars_container.add_widget(bar_row)

    bars_container.height = len(data_pairs) * dp(28)
    card.add_widget(bars_container)
    card.height = dp(80) + bars_container.height

    return card


class AnalyticsScreen(MDScreen):
    """Analytics dashboard with charts and summary cards."""

    def __init__(self, app: "FloraAdminApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._build()

    # ── build UI ────────────────────────────────────────────────────────
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
            text="Analytics",
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=0.7,
        ))
        header.add_widget(MDRaisedButton(
            text="Atualizar",
            size_hint_x=None,
            width=dp(120),
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.BG_BASE,
            on_release=lambda *a: self.load_data(),
        ))
        root.add_widget(header)

        # Content
        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(2))
        self._content = MDBoxLayout(
            orientation="vertical",
            spacing=Theme.SPACE_LG,
            padding=[0, 0, 0, Theme.SPACE_LG],
            size_hint_y=None,
        )
        self._content.bind(minimum_height=self._content.setter("height"))
        scroll.add_widget(self._content)
        root.add_widget(scroll)

        self.add_widget(root)

    def on_enter(self, *args):
        if not self._content.children:
            self.load_data()

    # ── data loading ─────────────────────────────────────────────────────
    def load_data(self):
        self._clear_content()
        spinner = MDSpinner(size_hint=(None, None), size=(dp(48), dp(48)))
        spinner.active = True
        self._content.add_widget(spinner)

        def _fetch():
            try:
                dashboard = self._app.api.get_analytics_dashboard()
                llm_usage = self._app.api.get_llm_usage()
                Clock.schedule_once(lambda dt: self._render(dashboard, llm_usage), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, e=e: self._show_error(str(e)), 0)

        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _render(self, dashboard: dict, llm_usage: dict):
        self._clear_content()

        messages = dashboard.get("messages", {})
        bots = dashboard.get("bots", {})
        users = dashboard.get("users", {})

        # ── Summary row ──────────────────────────────────────────────
        summary = MDBoxLayout(
            orientation="horizontal",
            spacing=Theme.SPACE_LG,
            size_hint_y=None,
            height=dp(96),
        )

        pairs = [
            ("Total Mensagens", messages.get("total", 0), f"{messages.get('today', 0)} hoje", "message-text", Colors.PRIMARY),
            ("Mensagens Semana", messages.get("week", 0), "últimos 7 dias", "email-multiple", Colors.WARNING),
            ("Total Bots",      bots.get("total", 0),        f"{bots.get('active', 0)} ativos", "robot", Colors.INFO),
            ("Usuários",        users.get("total", 0),       f"{users.get('active', 0)} ativos", "account-multiple", Colors.SUCCESS),
        ]

        for title, value, sub, icon, color in pairs:
            card = MDCard(
                orientation="horizontal",
                padding=Theme.SPACE_LG,
                spacing=Theme.SPACE_MD,
                md_bg_color=Colors.BG_CARD,
                radius=[Theme.RADIUS_LARGE],
                elevation=Theme.ELEVATION_LOW,
                size_hint_x=1,
                height=dp(96),
            )
            card.add_widget(MDIconButton(
                icon=icon,
                theme_text_color="Custom",
                text_color=color,
                user_font_size=dp(28),
                size_hint_x=None,
                width=dp(52),
            ))
            box = MDBoxLayout(orientation="vertical", spacing=dp(2))
            box.add_widget(MDLabel(
                text=title,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
            ))
            box.add_widget(MDLabel(
                text=str(value),
                font_style="H4",
                bold=True,
                theme_text_color="Custom",
                text_color=Colors.TEXT_PRIMARY,
            ))
            box.add_widget(MDLabel(
                text=sub,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
            ))
            card.add_widget(box)
            summary.add_widget(card)

        self._content.add_widget(summary)

        # ── LLM Usage chart (if available) ──────────────────────────
        llm_data = llm_usage.get("daily_usage", []) if isinstance(llm_usage, dict) else []
        if llm_data:
            chart_pairs = [
                (item.get("date", ""), item.get("tokens", 0))
                for item in llm_data
                if isinstance(item, dict)
            ]
            if chart_pairs:
                chart = _make_chart_card("Uso de LLM (tokens/dia)", chart_pairs, Colors.PRIMARY)
                self._content.add_widget(chart)

        # ── Messages by day (if available) ───────────────────────────
        msg_daily = dashboard.get("daily_messages", [])
        if msg_daily and isinstance(msg_daily, list):
            msg_pairs = [
                (item.get("date", ""), item.get("count", 0))
                for item in msg_daily
                if isinstance(item, dict)
            ]
            if msg_pairs:
                chart = _make_chart_card("Mensagens por Dia", msg_pairs, Colors.INFO)
                self._content.add_widget(chart)

    # ── helpers ──────────────────────────────────────────────────────────
    def _clear_content(self):
        self._content.clear_widgets()

    def _show_error(self, msg: str):
        self._clear_content()
        self._content.add_widget(MDLabel(
            text=f"Erro: {msg}",
            font_style="Body1",
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.HIGHLIGHT,
        ))
