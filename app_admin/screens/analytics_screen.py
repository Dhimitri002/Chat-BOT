"""
Analytics Screen for the Flora Admin Panel.
Analytics with charts, statistics, and date range filters.
"""
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout

from app_admin.services.api_client import api_client
from app_admin.utils.constants import Colors
from app_admin.utils.helpers import format_currency, format_number, format_datetime


class AnalyticsCard(MDCard):
    """A card displaying an analytics metric."""

    def __init__(self, title="", value="", subtitle="", icon="", color=None, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(4),
            md_bg_color=Colors.BG_CARD,
            radius=[dp(12)],
            elevation=dp(4),
            size_hint_y=None,
            height=dp(100),
            **kwargs,
        )

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(28),
            spacing=dp(8),
        )

        if icon:
            icon_btn = MDIconButton(
                icon=icon,
                icon_size=dp(20),
                theme_icon_color="Custom",
                icon_color=color or Colors.PRIMARY_LIGHT,
                size_hint_x=None,
                width=dp(32),
            )
            header.add_widget(icon_btn)

        title_label = MDLabel(
            text=title,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            valign="center",
        )
        header.add_widget(title_label)
        self.add_widget(header)

        # Value
        value_label = MDLabel(
            text=str(value),
            font_style="H4",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            bold=True,
        )
        self.add_widget(value_label)

        # Subtitle
        if subtitle:
            sub_label = MDLabel(
                text=subtitle,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                size_hint_y=None,
                height=dp(16),
            )
            self.add_widget(sub_label)


class ChartPlaceholder(MDCard):
    """A placeholder for charts."""

    def __init__(self, title="", description="", icon="chart-line", **kwargs):
        super().__init__(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            md_bg_color=Colors.BG_CARD,
            radius=[dp(12)],
            elevation=dp(4),
            size_hint_y=None,
            height=dp(250),
            **kwargs,
        )

        # Title
        title_label = MDLabel(
            text=f"[b]{title}[/b]",
            markup=True,
            font_style="H6",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(28),
        )
        self.add_widget(title_label)

        # Chart area
        chart_area = MDBoxLayout(
            orientation="vertical",
            padding=dp(20),
        )

        chart_icon = MDIconButton(
            icon=icon,
            icon_size=dp(48),
            theme_icon_color="Custom",
            icon_color=Colors.PRIMARY_LIGHT,
            pos_hint={"center_x": 0.5},
            disabled=True,
        )
        chart_area.add_widget(chart_icon)

        desc_label = MDLabel(
            text=description,
            halign="center",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
        )
        chart_area.add_widget(desc_label)

        # Simulated bar chart with colored bars
        bars_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(4),
            size_hint_y=None,
            height=dp(60),
            padding=[dp(20), 0],
        )

        bar_colors = Colors.CHART_COLORS
        bar_heights = [0.6, 0.8, 0.4, 0.9, 0.7, 0.5, 0.85]

        for i, (bh, bc) in enumerate(zip(bar_heights, bar_colors)):
            bar_container = MDBoxLayout(
                orientation="vertical",
                size_hint_x=1 / len(bar_heights),
            )
            bar_container.add_widget(MDBoxLayout(size_hint_y=1 - bh))
            bar = MDBoxLayout(
                md_bg_color=bc,
                radius=[dp(2), dp(2), 0, 0],
            )
            bar_container.add_widget(bar)
            bars_row.add_widget(bar_container)

        chart_area.add_widget(bars_row)
        self.add_widget(chart_area)


class AnalyticsScreen(MDScreen):
    """Analytics screen with charts and statistics."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "analytics"
        self._build_ui()

    def _build_ui(self):
        """Build the analytics screen UI."""
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
            text="Analises",
            font_style="H6",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            bold=True,
        )
        header.add_widget(header_title)

        header.add_widget(MDBoxLayout())

        refresh_btn = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color=Colors.TEXT_SECONDARY,
            on_release=self._load_analytics,
        )
        header.add_widget(refresh_btn)

        main_layout.add_widget(header)

        # Date range filter
        date_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(16), dp(4)],
            spacing=dp(8),
            md_bg_color=Colors.BG_DARK,
        )

        self.date_from_field = MDTextField(
            hint_text="Data inicial (DD/MM/AAAA)",
            mode="round",
            text="",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(8)],
            size_hint_x=0.4,
        )
        date_bar.add_widget(self.date_from_field)

        self.date_to_field = MDTextField(
            hint_text="Data final (DD/MM/AAAA)",
            mode="round",
            text="",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(8)],
            size_hint_x=0.4,
        )
        date_bar.add_widget(self.date_to_field)

        filter_btn = MDRaisedButton(
            text="Filtrar",
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=0.2,
            on_release=self._load_analytics,
        )
        date_bar.add_widget(filter_btn)

        main_layout.add_widget(date_bar)

        # Scrollable content
        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(4))

        content = MDBoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(16),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))

        # Key metrics row
        metrics_grid = MDGridLayout(
            cols=4,
            spacing=dp(12),
            size_hint_y=None,
            height=dp(112),
        )

        self.msg_card = AnalyticsCard(
            title="Mensagens",
            value="--",
            subtitle="Total no periodo",
            icon="message-text",
            color=Colors.SECONDARY,
        )
        metrics_grid.add_widget(self.msg_card)

        self.users_card = AnalyticsCard(
            title="Novos Usuarios",
            value="--",
            subtitle="No periodo",
            icon="account-plus",
            color=Colors.SUCCESS,
        )
        metrics_grid.add_widget(self.users_card)

        self.revenue_card = AnalyticsCard(
            title="Receita",
            value="--",
            subtitle="No periodo",
            icon="currency-usd",
            color=Colors.WARNING,
        )
        metrics_grid.add_widget(self.revenue_card)

        self.llm_card = AnalyticsCard(
            title="Custo LLM",
            value="--",
            subtitle="Tokens utilizados",
            icon="brain",
            color=Colors.TEAL,
        )
        metrics_grid.add_widget(self.llm_card)

        content.add_widget(metrics_grid)

        # Charts row
        charts_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(260),
        )

        msg_chart = ChartPlaceholder(
            title="Volume de Mensagens",
            description="Mensagens por dia no periodo",
            icon="chart-bar",
        )
        charts_row.add_widget(msg_chart)

        user_chart = ChartPlaceholder(
            title="Crescimento de Usuarios",
            description="Novos usuarios por dia",
            icon="chart-line",
        )
        charts_row.add_widget(user_chart)

        content.add_widget(charts_row)

        # Second charts row
        charts_row2 = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(260),
        )

        revenue_chart = ChartPlaceholder(
            title="Receita",
            description="Receita diaria no periodo",
            icon="chart-areaspline",
        )
        charts_row2.add_widget(revenue_chart)

        bot_chart = ChartPlaceholder(
            title="Uso de Bots",
            description="Bots mais ativos",
            icon="robot",
        )
        charts_row2.add_widget(bot_chart)

        content.add_widget(charts_row2)

        # LLM usage section
        llm_section = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            md_bg_color=Colors.BG_CARD,
            radius=[dp(12)],
            elevation=dp(4),
            size_hint_y=None,
            height=dp(200),
        )

        llm_title = MDLabel(
            text="[b]Uso de LLM[/b]",
            markup=True,
            font_style="H6",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(28),
        )
        llm_section.add_widget(llm_title)

        self.llm_details = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None,
            height=dp(140),
        )

        llm_fields = [
            ("Total de tokens", "--"),
            ("Tokens de entrada", "--"),
            ("Tokens de saida", "--"),
            ("Modelo mais usado", "--"),
            ("Custo total", "--"),
        ]

        self.llm_labels = {}
        for label_text, default_val in llm_fields:
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(28),
                spacing=dp(8),
            )
            row.add_widget(MDLabel(
                text=f"[b]{label_text}:[/b]",
                markup=True,
                font_style="Body2",
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
                size_hint_x=0.4,
            ))
            val_label = MDLabel(
                text=default_val,
                font_style="Body2",
                theme_text_color="Custom",
                text_color=Colors.TEXT_PRIMARY,
                size_hint_x=0.6,
            )
            row.add_widget(val_label)
            self.llm_labels[label_text] = val_label
            self.llm_details.add_widget(row)

        llm_section.add_widget(self.llm_details)
        content.add_widget(llm_section)

        # Loading
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
        nav_drawer = self.manager.parent.ids.get("nav_drawer") if hasattr(self.manager.parent, "ids") else None
        if nav_drawer:
            nav_drawer.set_state("open")

    def on_pre_enter(self):
        self._load_analytics()

    def _load_analytics(self, *args):
        """Load analytics data from API."""
        self.loading_box.height = dp(60)
        self.loading_spinner.active = True

        def _on_data(result, error):
            self.loading_box.height = dp(0)
            self.loading_spinner.active = False

            if error:
                return

            if result:
                self._update_metrics(result)
                self._update_llm_details(result)

        date_from = self.date_from_field.text.strip()
        date_to = self.date_to_field.text.strip()
        api_client.get_analytics_async(
            _on_data,
            date_from=date_from,
            date_to=date_to,
        )

    def _update_metrics(self, data):
        """Update metric cards."""
        if "total_messages" in data:
            self.msg_card.children[1].text = format_number(data["total_messages"])
        if "new_users" in data:
            self.users_card.children[1].text = format_number(data["new_users"])
        if "revenue" in data:
            self.revenue_card.children[1].text = format_currency(data["revenue"])
        if "llm_cost" in data:
            self.llm_card.children[1].text = format_currency(data["llm_cost"])

    def _update_llm_details(self, data):
        """Update LLM usage details."""
        llm_data = data.get("llm_usage", {})
        if not llm_data:
            return

        mappings = {
            "Total de tokens": format_number(llm_data.get("total_tokens", 0)),
            "Tokens de entrada": format_number(llm_data.get("input_tokens", 0)),
            "Tokens de saida": format_number(llm_data.get("output_tokens", 0)),
            "Modelo mais usado": llm_data.get("most_used_model", "N/A"),
            "Custo total": format_currency(llm_data.get("total_cost", 0)),
        }

        for label, value in mappings.items():
            if label in self.llm_labels:
                self.llm_labels[label].text = value
