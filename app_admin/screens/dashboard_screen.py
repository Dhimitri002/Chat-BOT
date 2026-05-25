"""
DashboardScreen — Central admin overview.

Displays platform-wide stats fetched from GET /api/v1/admin/dashboard.
The backend returns:
  {
    "users":         { "total": N, "active": N, "new_today": N, "new_week": N },
    "bots":          { "total": N, "active": N, "inactive": N },
    "messages":      { "total": N, "today": N, "week": N },
    "whatsapp":      { "total_sessions": N, "connected": N, "disconnected": N },
    "licenses":      { "total": N, "active": N, "expired": N, "revoked": N },
    "subscriptions": { "total": N, "active": N },
    "recent_events": [ { "type": str, "message": str, "created_at": str } ]
  }
"""

from kivy.metrics import dp
from kivy.properties import DictProperty
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.button import MDIconButton

from app_admin.styles.theme import Colors, Theme


# ── helper: build a single stat card ────────────────────────────────────
def _make_stat_card(title: str, value: str, subtitle: str, icon: str, accent_color) -> MDCard:
    card = MDCard(
        orientation="horizontal",
        padding=Theme.SPACE_LG,
        spacing=Theme.SPACE_LG,
        md_bg_color=Colors.BG_CARD,
        radius=[Theme.RADIUS_LARGE],
        elevation=Theme.ELEVATION_LOW,
        size_hint_y=None,
        height=dp(96),
    )

    icon_btn = MDIconButton(
        icon=icon,
        theme_text_color="Custom",
        text_color=accent_color,
        user_font_size=dp(32),
        size_hint_x=None,
        width=dp(56),
    )
    card.add_widget(icon_btn)

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
        text=subtitle,
        font_style="Caption",
        theme_text_color="Custom",
        text_color=Colors.TEXT_SECONDARY,
    ))
    card.add_widget(box)
    return card


class DashboardScreen(MDScreen):
    """Admin dashboard: stat cards + recent events feed."""

    def __init__(self, app: "FloraAdminApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._dashboard_data: dict = {}
        self._build()

    # ── build UI ────────────────────────────────────────────────────────
    def _build(self):
        root = MDBoxLayout(
            orientation="vertical",
            padding=Theme.SPACE_LG,
            spacing=Theme.SPACE_LG,
            md_bg_color=Colors.BG_BASE,
        )

        # Scrollable content area
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

        # Loading spinner (shown by default)
        self._spinner = MDSpinner(size_hint=(None, None), size=(dp(48), dp(48)))
        self._center_loading = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            padding=[0, 0],
        )
        self._center_loading.add_widget(MDBoxLayout())
        self._center_loading.add_widget(self._spinner)
        self._center_loading.add_widget(MDBoxLayout())

    def on_enter(self, *args):
        self.load_data()

    # ── data loading ─────────────────────────────────────────────────────
    def load_data(self):
        self._clear_content()
        self._content.add_widget(self._center_loading)
        self._spinner.active = True

        def _fetch():
            try:
                data = self._app.api.get_admin_dashboard()
                Clock.schedule_once(lambda dt: self._render_safe(data), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, e=e: self._show_error(str(e)), 0)
            finally:
                self._spinner.active = False

        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _render_safe(self, data: dict):
        try:
            self._render(data)
        except Exception as e:
            self._show_error(str(e))

    # ── rendering ────────────────────────────────────────────────────────
    def _render(self, data: dict):
        self._dashboard_data = data
        self._clear_content()

        users        = data.get("users", {})
        bots         = data.get("bots", {})
        messages     = data.get("messages", {})
        whatsapp     = data.get("whatsapp", {})
        licenses     = data.get("licenses", {})
        subscriptions = data.get("subscriptions", {})
        recent_events = data.get("recent_events", [])

        # ── row 1: core metrics ────────────────────────────────────────
        row1 = MDBoxLayout(
            orientation="horizontal",
            spacing=Theme.SPACE_LG,
            size_hint_y=None,
            height=dp(96),
        )
        for title, value, sub, icon, color in [
            ("Usuários",          users.get("total", 0), f"{users.get('active', 0)} ativos", "account-multiple", Colors.PRIMARY),
            ("Bots",              bots.get("total", 0),  f"{bots.get('active', 0)} ativos",  "robot",            Colors.INFO),
            ("Mensagens",         messages.get("total", 0), f"{messages.get('today', 0)} hoje", "message-text", Colors.WARNING),
            ("Licenças",          licenses.get("total", 0), f"{licenses.get('active', 0)} ativas", "certificate", Colors.SUCCESS),
        ]:
            row1.add_widget(_make_stat_card(title, value, sub, icon, color))
        self._content.add_widget(row1)

        # ── row 2: secondary metrics ───────────────────────────────────
        row2 = MDBoxLayout(
            orientation="horizontal",
            spacing=Theme.SPACE_LG,
            size_hint_y=None,
            height=dp(96),
        )
        for title, value, sub, icon, color in [
            ("WhatsApp Sessions", whatsapp.get("total_sessions", 0), f"{whatsapp.get('connected', 0)} conectadas", "whatsapp", Colors.PRIMARY),
            ("Novos Usuários",    users.get("new_week", 0), "esta semana",          "account-plus", Colors.HIGHLIGHT),
            ("Mensagens Semana",  messages.get("week", 0), "últimos 7 dias",       "email-multiple", Colors.INFO),
            ("Assinaturas",       subscriptions.get("active", 0), f"{subscriptions.get('total', 0)} totails", "credit-card", Colors.WARNING),
        ]:
            row2.add_widget(_make_stat_card(title, value, sub, icon, color))
        self._content.add_widget(row2)

        # ── Recent events section ──────────────────────────────────────
        events_title = MDLabel(
            text="Eventos Recentes",
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(40),
        )
        self._content.add_widget(events_title)

        if not recent_events:
            empty = MDLabel(
                text="Nenhum evento recente.",
                font_style="Body2",
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                halign="center",
                size_hint_y=None,
                height=dp(40),
            )
            self._content.add_widget(empty)
        else:
            events_card = MDCard(
                orientation="vertical",
                padding=Theme.SPACE_MD,
                spacing=dp(4),
                md_bg_color=Colors.BG_CARD,
                radius=[Theme.RADIUS_LARGE],
                elevation=Theme.ELEVATION_LOW,
                size_hint_y=None,
            )
            events_card.bind(
                minimum_height=events_card.setter("height")
            )

            for evt in recent_events[:20]:
                row = MDBoxLayout(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(36),
                    padding=[Theme.SPACE_SM, 0],
                    spacing=dp(8),
                )
                icon_name = "information"
                icon_color = Colors.TEXT_SECONDARY
                evt_type = evt.get("type", "")
                if "error" in evt_type.lower() or "fail" in evt_type.lower():
                    icon_name = "alert-circle"
                    icon_color = Colors.HIGHLIGHT
                elif "warning" in evt_type.lower():
                    icon_name = "alert"
                    icon_color = Colors.WARNING
                elif "success" in evt_type.lower() or "login" in evt_type.lower():
                    icon_name = "check-circle"
                    icon_color = Colors.SUCCESS

                row.add_widget(MDIconButton(
                    icon=icon_name,
                    theme_text_color="Custom",
                    text_color=icon_color,
                    size_hint_x=None,
                    width=dp(36),
                ))
                row.add_widget(MDLabel(
                    text=evt.get("message", ""),
                    font_style="Body2",
                    theme_text_color="Custom",
                    text_color=Colors.TEXT_PRIMARY,
                    shorten=True,
                ))
                events_card.add_widget(row)

            self._content.add_widget(events_card)

    # ── helpers ──────────────────────────────────────────────────────────
    def _clear_content(self):
        self._content.clear_widgets()

    def _show_error(self, msg: str):
        self._clear_content()
        self._content.add_widget(MDLabel(
            text=f"Erro ao carregar: {msg}",
            font_style="Body1",
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.HIGHLIGHT,
        ))
