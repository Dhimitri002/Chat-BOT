"""
Flora Admin — Tela de Analytics
==================================
Dashboard de métricas: mensagens, usuários, bots, receita.
Gráficos de linha e barras com dados da API.
"""

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from apps.shared.theme import FloraColors, FloraTheme


class AnalyticsScreen(MDScreen):
    """Tela de analytics e métricas da plataforma."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        c = FloraColors()
        layout = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        # Header
        header = MDBoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        title = MDLabel(
            text="📊  Analytics",
            font_style="H4",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
            bold=True,
        )
        header.add_widget(title)
        layout.add_widget(header)

        # Period selector
        period_bar = MDBoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        for period in ["7 dias", "30 dias", "90 dias", "Tudo"]:
            chip = MDLabel(
                text=period,
                theme_text_color="Custom",
                text_color=c.to_rgba(c.TEXT_SECONDARY),
                font_style="Caption",
                halign="center",
                size_hint_x=0.25,
            )
            period_bar.add_widget(chip)
        layout.add_widget(period_bar)

        # Stats cards grid (2x2)
        stats_grid = MDBoxLayout(orientation="vertical", spacing=dp(12))

        row1 = MDBoxLayout(spacing=dp(12))
        row1.add_widget(self._build_stat_card("💬 Mensagens", "12.456", "+18%", c.PRIMARY_PURPLE))
        row1.add_widget(self._build_stat_card("👥 Usuários", "847", "+12%", c.ACCENT_PINK))
        stats_grid.add_widget(row1)

        row2 = MDBoxLayout(spacing=dp(12))
        row2.add_widget(self._build_stat_card("🤖 Bots Ativos", "234", "+5%", c.SUCCESS))
        row2.add_widget(self._build_stat_card("💰 Receita", "R$ 18.450", "+24%", c.WARNING))
        stats_grid.add_widget(row2)

        layout.add_widget(stats_grid)

        # Charts section
        charts_title = MDLabel(
            text="[b]Tendências[/b]",
            font_style="H5",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
            bold=True,
            markup=True,
            size_hint_y=None,
            height=dp(40),
        )
        layout.add_widget(charts_title)

        # Message volume chart placeholder
        chart_card = self._build_chart_card("Volume de Mensagens (30 dias)")
        layout.add_widget(chart_card)

        # User growth chart
        growth_card = self._build_chart_card("Crescimento de Usuários (30 dias)")
        layout.add_widget(growth_card)

        # Top bots section
        top_bots_title = MDLabel(
            text="[b]Top Bots por Mensagens[/b]",
            font_style="H5",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
            bold=True,
            markup=True,
            size_hint_y=None,
            height=dp(40),
        )
        layout.add_widget(top_bots_title)

        top_bots_card = self._build_top_bots()
        layout.add_widget(top_bots_card)

        # Bottom spacing
        layout.add_widget(MDBoxLayout(size_hint_y=None, height=dp(80)))

        self.add_widget(layout)

    def _build_stat_card(self, label: str, value: str, trend: str, color_hex: str) -> MDCard:
        c = FloraColors()
        card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(4),
            size_hint_x=0.5,
            radius=[FloraTheme.CARD_RADIUS],
            elevation=FloraTheme.CARD_ELEVATION,
            md_bg_color=c.to_rgba(c.SURFACE_CARD),
        )

        lbl = MDLabel(
            text=label,
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_SECONDARY),
            font_style="Caption",
        )
        card.add_widget(lbl)

        val = MDLabel(
            text=f"[b]{value}[/b]",
            font_style="H4",
            theme_text_color="Custom",
            text_color=c.to_rgba(color_hex),
            bold=True,
            markup=True,
        )
        card.add_widget(val)

        trend_color = c.SUCCESS if "+" in trend else c.ERROR
        trend_lbl = MDLabel(
            text=trend,
            theme_text_color="Custom",
            text_color=c.to_rgba(trend_color),
            font_style="Caption",
        )
        card.add_widget(trend_lbl)

        return card

    def _build_chart_card(self, title: str) -> MDCard:
        c = FloraColors()
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

        title_lbl = MDLabel(
            text=title,
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
            font_style="Body",
            bold=True,
            size_hint_y=None,
            height=dp(24),
        )
        card.add_widget(title_lbl)

        # Simple bar chart representation using BoxLayout
        bar_area = MDBoxLayout(spacing=dp(4), padding=[0, dp(20), 0, 0])
        bar_colors = [c.PRIMARY_PURPLE, c.ACCENT_PURPLE_LIGHT, c.ACCENT_PINK, c.PRIMARY_PURPLE]
        bar_values = [0.6, 0.8, 0.45, 0.9, 0.7, 0.55, 0.85, 0.5, 0.75, 0.65, 0.95, 0.4]
        import random
        random.seed(42)

        for i, val in enumerate(bar_values):
            bar_container = MDBoxLayout(orientation="vertical")
            # This is a simplified bar - in production use a proper charting library
            bar = MDBoxLayout(
                size_hint_y=val,
                md_bg_color=c.to_rgba(c.PRIMARY_PURPLE if i % 2 == 0 else c.ACCENT_PINK),
            )
            spacer = MDBoxLayout(size_hint_y=1 - val)
            bar_container.add_widget(spacer)
            bar_container.add_widget(bar)
            bar_area.add_widget(bar_container)

        card.add_widget(bar_area)
        return card

    def _build_top_bots(self) -> MDCard:
        c = FloraColors()
        card = MDCard(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(4),
            size_hint_y=None,
            height=dp(200),
            radius=[FloraTheme.CARD_RADIUS],
            elevation=FloraTheme.CARD_ELEVATION,
            md_bg_color=c.to_rgba(c.SURFACE_CARD),
        )

        bots = [
            ("🤖 Atendimento Bot", "3.245 msgs"),
            ("📱 Suporte Plus", "2.890 msgs"),
            ("💬 Vendas Express", "2.156 msgs"),
            ("🎯 Lead Capture", "1.847 msgs"),
            ("📊 Report Bot", "1.523 msgs"),
        ]

        for name, count in bots:
            row = MDBoxLayout(size_hint_y=None, height=dp(32), spacing=dp(8))
            name_lbl = MDLabel(
                text=name,
                theme_text_color="Custom",
                text_color=c.to_rgba(c.TEXT_PRIMARY),
                font_style="Body",
                size_hint_x=0.7,
            )
            row.add_widget(name_lbl)
            count_lbl = MDLabel(
                text=count,
                theme_text_color="Custom",
                text_color=c.to_rgba(c.TEXT_SECONDARY),
                font_style="Body",
                halign="right",
                size_hint_x=0.3,
            )
            row.add_widget(count_lbl)
            card.add_widget(row)

        return card
