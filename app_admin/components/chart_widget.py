"""
Simple chart widgets using Kivy Canvas for lightweight bar / line charts.

No matplotlib dependency needed — pure Kivy drawing.
"""
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.properties import (
    ListProperty,
    NumericProperty,
    StringProperty,
    BooleanProperty,
)
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.widget import Widget

from app_admin.utils.constants import Colors
from app_admin.styles.theme import Theme


class SimpleBarChart(MDCard):
    """Horizontal/vertical bar chart drawn on canvas."""

    title = StringProperty("Grafico")
    data = ListProperty([])       # list of {"label": str, "value": float}
    max_value = NumericProperty(0)  # if 0, auto-computed
    bar_color = ListProperty(Colors.PRIMARY_LIGHT)
    show_values = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=Theme.SPACE_XL,
            spacing=Theme.SPACE_SM,
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_LARGE],
            elevation=Theme.ELEVATION_MEDIUM,
            **kwargs,
        )
        self._build()

    def _build(self):
        self._title_label = MDLabel(
            text=self.title,
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(24),
        )
        self.add_widget(self._title_label)

        # Chart drawing area
        self._chart_area = Widget()
        self.add_widget(self._chart_area)
        self._chart_area.bind(pos=self._draw, size=self._draw)
        self.bind(data=self._draw, max_value=self._draw)

    def _draw(self, *args):
        self._chart_area.canvas.clear()
        if not self.data:
            return

        mx = self.max_value if self.max_value else max(d["value"] for d in self.data)
        if mx == 0:
            return

        n = len(self.data)
        padding = dp(12)
        label_h = dp(20)
        gap = dp(8)
        available_h = self._chart_area.height - padding * 2 - label_h
        bar_h = min(dp(24), (available_h - gap * (n - 1)) / n)

        with self._chart_area.canvas:
            for i, item in enumerate(self.data):
                ratio = item["value"] / mx
                bar_w = max(dp(2), (self._chart_area.width - padding * 2 - dp(80)) * ratio)
                y = padding + (bar_h + gap) * (n - 1 - i)

                # Bar fill
                c = self.bar_color if len(self.bar_color) == 4 else (*self.bar_color[:3], 1)
                Color(*c)
                Rectangle(pos=(self._chart_area.x + padding + dp(70), y + dp(4)),
                          size=(bar_w, bar_h - dp(8)))

                # Label (right of bar, drawn in _draw_text via MDLabel approach is
                # complex; we rely on the bar visuals and the title area above)
                if self.show_values:
                    val_str = str(item["value"])
                    # Small dot indicator instead of text in canvas
                    Color(1, 1, 1, 0.6)
                    Ellipse(pos=(self._chart_area.x + padding + dp(70) + bar_w + dp(4),
                                 y + bar_h / 2 - dp(3)),
                             size=(dp(6), dp(6)))

    def on_title(self, _inst, val):
        if hasattr(self, "_title_label"):
            self._title_label.text = val


class SimpleLineChart(MDCard):
    """Simple line chart drawn on canvas."""

    title = StringProperty("Grafico de Linha")
    data = ListProperty([])       # list of {"label": str, "value": float}
    line_color = ListProperty(Colors.TEAL)
    fill_area = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=Theme.SPACE_XL,
            spacing=Theme.SPACE_SM,
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_LARGE],
            elevation=Theme.ELEVATION_MEDIUM,
            **kwargs,
        )
        self._build()

    def _build(self):
        self._title_label = MDLabel(
            text=self.title,
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(24),
        )
        self.add_widget(self._title_label)

        self._chart_area = Widget()
        self.add_widget(self._chart_area)
        self._chart_area.bind(pos=self._draw, size=self._draw)
        self.bind(data=self._draw)

    def _draw(self, *args):
        self._chart_area.canvas.clear()
        if not self.data or len(self.data) < 2:
            return

        values = [d["value"] for d in self.data]
        mx = max(values)
        mn = min(values)
        rg = mx - mn if mx != mn else 1

        pad = dp(16)
        w = self._chart_area.width - pad * 2
        h = self._chart_area.height - pad * 2

        points = []
        for i, v in enumerate(values):
            x = self._chart_area.x + pad + w * i / max(len(values) - 1, 1)
            y = self._chart_area.y + pad + h * (v - mn) / rg
            points.extend([x, y])

        with self._chart_area.canvas:
            if self.fill_area:
                # Fill area under line
                fill_pts = list(points)
                fill_pts.extend([
                    self._chart_area.x + pad + w,
                    self._chart_area.y + pad,
                    self._chart_area.x + pad,
                    self._chart_area.y + pad,
                ])
                c = self.line_color[:3] if len(self.line_color) >= 3 else self.line_color
                Color(c[0], c[1], c[2], 0.15)
                Line(points=fill_pts, close=True, width=1)

            # Line
            c = self.line_color if len(self.line_color) >= 3 else (*self.line_color, 1)[:3]
            Color(c[0], c[1], c[2], 1)
            Line(points=points, width=dp(2))

            # Dots
            for i in range(0, len(points), 2):
                Color(c[0], c[1], c[2], 0.8)
                Ellipse(pos=(points[i] - dp(4), points[i + 1] - dp(4)),
                         size=(dp(8), dp(8)))

    def on_title(self, _inst, val):
        if hasattr(self, "_title_label"):
            self._title_label.text = val
