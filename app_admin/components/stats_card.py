"""
StatsCard — A reusable card widget for displaying a key metric.

Usage:
    StatsCard(
        title="Total Bots",
        value="42",
        subtitle="+12 este mes",
        icon="robot",
        icon_color=(0.4, 0.8, 0.4, 1),
    )
"""
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import (
    StringProperty,
    NumericProperty,
    ListProperty,
    ObjectProperty,
)
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton

from app_admin.utils.constants import Colors
from app_admin.styles.theme import Theme


class StatsCard(MDCard):
    """Card that displays a single statistic with icon, value, and subtitle."""

    title = StringProperty("")
    value = StringProperty("0")
    subtitle = StringProperty("")
    icon = StringProperty("chart-box")
    icon_color = ListProperty(Colors.PRIMARY_LIGHT)
    value_color = ListProperty(Colors.TEXT_PRIMARY)
    trend = NumericProperty(0)  # positive = up, negative = down, 0 = flat

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=Theme.SPACE_LG,
            spacing=dp(4),
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_LARGE],
            elevation=Theme.ELEVATION_MEDIUM,
            size_hint_y=None,
            height=dp(120),
            **kwargs,
        )
        self._build()

    def _build(self):
        # Top row: icon + optional trend
        top_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
            spacing=dp(4),
        )

        self._icon_btn = MDIconButton(
            icon=self.icon,
            icon_size=dp(24),
            theme_icon_color="Custom",
            icon_color=self.icon_color,
            size_hint_x=None,
            width=dp(40),
            disabled=True,
        )
        top_row.add_widget(self._icon_btn)

        top_row.add_widget(MDBoxLayout())  # spacer

        if self.trend != 0:
            trend_icon = "trending-up" if self.trend > 0 else "trending-down"
            trend_color = Colors.SUCCESS if self.trend > 0 else Colors.ERROR
            trend_label = MDLabel(
                text=f"{trend_icon} {abs(self.trend):.0f}%",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=trend_color,
                halign="right",
                size_hint_x=None,
                width=dp(60),
            )
            top_row.add_widget(trend_label)

        self.add_widget(top_row)

        # Value
        self._value_label = MDLabel(
            text=self.value,
            font_style="H4",
            bold=True,
            theme_text_color="Custom",
            text_color=self.value_color,
            size_hint_y=None,
            height=dp(36),
        )
        self.add_widget(self._value_label)

        # Title
        self._title_label = MDLabel(
            text=self.title,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(18),
        )
        self.add_widget(self._title_label)

        # Subtitle (optional)
        if self.subtitle:
            self._subtitle_label = MDLabel(
                text=self.subtitle,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                size_hint_y=None,
                height=dp(16),
            )
            self.add_widget(self._subtitle_label)

    def animate_in(self, delay=0):
        """Fade-in animation with slight upward movement."""
        self.opacity = 0
        self.y += dp(10)
        from app_admin.styles.theme import Anim
        anim = Animation(opacity=1, y=self.y - dp(10), duration=Anim.NORMAL)
        if delay:
            Clock.schedule_once(lambda dt: anim.start(self), delay)
        else:
            anim.start(self)

    # --- Property bindings ---
    def on_value(self, _inst, val):
        if hasattr(self, "_value_label"):
            self._value_label.text = str(val)

    def on_title(self, _inst, val):
        if hasattr(self, "_title_label"):
            self._title_label.text = str(val)

    def on_icon(self, _inst, val):
        if hasattr(self, "_icon_btn"):
            self._icon_btn.icon = val

    def on_icon_color(self, _inst, val):
        if hasattr(self, "_icon_btn"):
            self._icon_btn.icon_color = val
