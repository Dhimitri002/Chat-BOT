"""
Dashboard Screen for the Flora Admin Panel.
Main admin dashboard with stats, charts, and activity feed.
"""
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout

from app_admin.services.api_client import api_client
from app_admin.utils.constants import Colors
from app_admin.utils.helpers import format_currency, format_number, time_ago


class StatCard(MDCard):
    """A card displaying a single statistic."""

    def __init__(self, title="", value="", icon="", color=None, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            md_bg_color=Colors.BG_CARD,
            radius=[dp(12)],
            elevation=dp(4),
            size_hint_y=None,
            height=dp(120),
            **kwargs,
        )
        self._build(title, value, icon, color)

    def _build(self, title, value, icon, color):
        # Top row: icon and title
        top_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
            spacing=dp(8),
        )

        icon_btn = MDIconButton(
            icon=icon,
            icon_size=dp(24),
            theme_icon_color="Custom",
            icon_color=color or Colors.PRIMARY_LIGHT,
        )
        top_row.add_widget(icon_btn)

        title_label = MDLabel(
            text=title,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            valign="center",
        )
        top_row.add_widget(title_label)
        self.add_widget(top_row)

        # Value
        self.value_label = MDLabel(
            text=str(value),
            font_style="H4",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            bold=True,
        )
        self.add_widget(self.value_label)

    def update_value(self, value):
        self.value_label.text = str(value)


class ActivityItem(MDCard):
    """A single activity feed item."""

    def __init__(self, message="", timestamp="", icon="information", color=None, **kwargs):
        super().__init__(
            orientation="horizontal",
            padding=dp(12),
            spacing=dp(12),
            md_bg_color=Colors.BG_SURFACE,
            radius=[dp(8)],
            elevation=dp(1),
            size_hint_y=None,
            height=dp(60),
            **kwargs,
        )

        icon_btn = MDIconButton(
            icon=icon,
            icon_size=dp(20),
            theme_icon_color="Custom",
            icon_color=color or Colors.INFO,
            size_hint_x=None,
            width=dp(40),
        )
        self.add_widget(icon_btn)

        content = MDBoxLayout(orientation="vertical", spacing=dp(2))
        msg_label = MDLabel(
            text=message,
            font_style="Body2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            shorten=True,
            shorten_from="right",
        )
        content.add_widget(msg_label)

        time_label = MDLabel(
            text=timestamp,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
        )
        content.add_widget(time_label)
        self.add_widget(content)


class DashboardScreen(MDScreen):
    """Main admin dashboard screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "dashboard"
        self._build_ui()
        self._stat_cards = {}

    def _build_ui(self):
        """Build the dashboard UI."""
        main_layout = MDBoxLayout(
            orientation="vertical",
            md_bg_color=Colors.BG_DARK,
        )

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            padding=[dp(16), dp(8)],
            spacing=dp(8),
            md_bg_color=Colors.BG_CARD,
        )

        menu_btn = MDIconButton(
            icon="menu",
            theme_icon_color="Custom",
            icon_color=Colors.TEXT_PRIMARY,
            on_release=self._open_drawer,
        )
        header.add_widget(menu_btn)

        header_title = MDLabel(
            text="Painel de Controle",
            font_style="H6",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            bold=True,
        )
        header.add_widget(header_title)

        header.add_widget(MDBoxLayout())  # Spacer

        refresh_btn = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color=Colors.TEXT_SECONDARY,
            on_refresh=self._refresh_data,
        )
        header.add_widget(refresh_btn)

        main_layout.add_widget(header)

        # Scrollable content
        scroll = MDScrollView(
            do_scroll_x=False,
            bar_width=dp(4),
            bar_color=Colors.PRIMARY,
            bar_inactive_color=Colors.BG_SURFACE,
        )

        content = MDBoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(16),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))

        # Stats cards grid
        stats_grid = MDGridLayout(
            cols=4,
            spacing=dp(12),
            size_hint_y=None,
            height=dp(132),
            padding=[0, 0],
        )

        self._stat_cards["users"] = StatCard(
            title="Total de Usuarios",
            value="--",
            icon="account-group",
            color=Colors.SECONDARY,
        )
        stats_grid.add_widget(self._stat_cards["users"])

        self._stat_cards["bots"] = StatCard(
            title="Bots Ativos",
            value="--",
            icon="robot",
            color=Colors.SUCCESS,
        )
        stats_grid.add_widget(self._stat_cards["bots"])

        self._stat_cards["revenue"] = StatCard(
            title="Receita Mensal",
            value="--",
            icon="currency-usd",
            color=Colors.WARNING,
        )
        stats_grid.add_widget(self._stat_cards["revenue"])

        self._stat_cards["sessions"] = StatCard(
            title="Sessoes Ativas",
            value="--",
            icon="whatsapp",
            color=Colors.TEAL,
        )
        stats_grid.add_widget(self._stat_cards["sessions"])

        content.add_widget(stats_grid)

        # Middle row: Charts and Activity
        middle_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(300),
        )

        # Chart placeholder card
        chart_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            md_bg_color=Colors.BG_CARD,
            radius=[dp(12)],
            elevation=dp(4),
            size_hint_x=0.6,
        )

        chart_header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
        )
        chart_title = MDLabel(
            text="Volume de Mensagens",
            font_style="H6",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            bold=True,
        )
        chart_header.add_widget(chart_title)
        chart_card.add_widget(chart_header)

        # Chart placeholder
        chart_placeholder = MDBoxLayout(
            orientation="vertical",
            padding=dp(20),
        )
        chart_icon = MDIconButton(
            icon="chart-bar",
            icon_size=dp(64),
            theme_icon_color="Custom",
            icon_color=Colors.PRIMARY_LIGHT,
            pos_hint={"center_x": 0.5},
            disabled=True,
        )
        chart_placeholder.add_widget(chart_icon)

        chart_info = MDLabel(
            text="Grafico de mensagens dos ultimos 7 dias",
            halign="center",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
        )
        chart_placeholder.add_widget(chart_info)

        chart_card.add_widget(chart_placeholder)
        middle_row.add_widget(chart_card)

        # Activity feed card
        activity_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            md_bg_color=Colors.BG_CARD,
            radius=[dp(12)],
            elevation=dp(4),
            size_hint_x=0.4,
        )

        activity_header = MDLabel(
            text="Atividade Recente",
            font_style="H6",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            bold=True,
            size_hint_y=None,
            height=dp(32),
        )
        activity_card.add_widget(activity_header)

        self.activity_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
        )
        self.activity_list.bind(minimum_height=self.activity_list.setter("height"))

        activity_scroll = MDScrollView(do_scroll_x=False, bar_width=dp(2))
        activity_scroll.add_widget(self.activity_list)
        activity_card.add_widget(activity_scroll)

        middle_row.add_widget(activity_card)
        content.add_widget(middle_row)

        # Quick actions
        actions_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12),
            md_bg_color=Colors.BG_CARD,
            radius=[dp(12)],
            elevation=dp(4),
            size_hint_y=None,
            height=dp(120),
        )

        actions_title = MDLabel(
            text="Acoes Rapidas",
            font_style="H6",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            bold=True,
            size_hint_y=None,
            height=dp(24),
        )
        actions_card.add_widget(actions_title)

        actions_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(48),
        )

        btn_users = MDRaisedButton(
            text="Usuarios",
            icon="account-group",
            md_bg_color=Colors.SECONDARY,
            text_color=Colors.TEXT_PRIMARY,
            on_release=lambda x: self._navigate_to("users"),
        )
        actions_row.add_widget(btn_users)

        btn_bots = MDRaisedButton(
            text="Bots",
            icon="robot",
            md_bg_color=Colors.SUCCESS,
            text_color=Colors.TEXT_PRIMARY,
            on_release=lambda x: self._navigate_to("bots"),
        )
        actions_row.add_widget(btn_bots)

        btn_plans = MDRaisedButton(
            text="Planos",
            icon="package-variant",
            md_bg_color=Colors.WARNING,
            text_color=Colors.TEXT_PRIMARY,
            on_release=lambda x: self._navigate_to("plans"),
        )
        actions_row.add_widget(btn_plans)

        btn_licenses = MDRaisedButton(
            text="Licencas",
            icon="key-variant",
            md_bg_color=Colors.TEAL,
            text_color=Colors.TEXT_PRIMARY,
            on_release=lambda x: self._navigate_to("licenses"),
        )
        actions_row.add_widget(btn_licenses)

        actions_card.add_widget(actions_row)
        content.add_widget(actions_card)

        # Loading overlay
        self.loading_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(0),
            padding=dp(16),
        )
        self.loading_spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            active=False,
            color=Colors.PRIMARY_LIGHT,
            pos_hint={"center_x": 0.5},
        )
        self.loading_box.add_widget(self.loading_spinner)
        content.add_widget(self.loading_box)

        scroll.add_widget(content)
        main_layout.add_widget(scroll)
        self.add_widget(main_layout)

    def _open_drawer(self, *args):
        """Open the navigation drawer."""
        nav_drawer = self.manager.parent.ids.get("nav_drawer") if hasattr(self.manager.parent, "ids") else None
        if nav_drawer:
            nav_drawer.set_state("open")

    def _navigate_to(self, screen_name):
        """Navigate to another screen."""
        self.manager.current = screen_name

    def _refresh_data(self, *args):
        """Refresh dashboard data."""
        self._load_data()

    def on_pre_enter(self):
        """Called when screen is about to be entered."""
        self._load_data()

    def _load_data(self):
        """Load dashboard data from API."""
        self.loading_box.height = dp(60)
        self.loading_spinner.active = True

        def _on_data(result, error):
            self.loading_box.height = dp(0)
            self.loading_spinner.active = False

            if error:
                self._show_error(str(error))
                return

            if result:
                self._update_stats(result)
                self._update_activity(result)

        api_client.get_dashboard_async(_on_data)

    def _update_stats(self, data):
        """Update stat cards with data."""
        if "total_users" in data:
            self._stat_cards["users"].update_value(format_number(data["total_users"]))
        if "active_bots" in data:
            self._stat_cards["bots"].update_value(format_number(data["active_bots"]))
        if "monthly_revenue" in data:
            self._stat_cards["revenue"].update_value(format_currency(data["monthly_revenue"]))
        if "active_sessions" in data:
            self._stat_cards["sessions"].update_value(format_number(data["active_sessions"]))

    def _update_activity(self, data):
        """Update activity feed."""
        self.activity_list.clear_widgets()
        activities = data.get("recent_activity", [])

        if not activities:
            # Show placeholder
            placeholder = MDLabel(
                text="Nenhuma atividade recente",
                halign="center",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                size_hint_y=None,
                height=dp(40),
            )
            self.activity_list.add_widget(placeholder)
            return

        for activity in activities[:10]:
            item = ActivityItem(
                message=activity.get("message", ""),
                timestamp=time_ago(activity.get("timestamp")),
                icon=activity.get("icon", "information"),
                color=activity.get("color"),
            )
            self.activity_list.add_widget(item)

    def _show_error(self, message):
        """Show error in activity area."""
        self.activity_list.clear_widgets()
        error_item = ActivityItem(
            message=f"Erro ao carregar dados: {message}",
            timestamp="Agora",
            icon="alert-circle",
            color=Colors.ERROR,
        )
        self.activity_list.add_widget(error_item)
