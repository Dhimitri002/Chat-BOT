"""Status Card - Cartao de status reutilizavel."""
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty
from kivy.utils import get_color_from_hex
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout


class StatusCard(MDCard):
    """Cartao de status com icone, titulo, valor e cor de status."""

    title = StringProperty("")
    value = StringProperty("")
    icon = StringProperty("information")
    status_color = StringProperty("#4ecca3")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.spacing = dp(12)
        self.padding = dp(16)
        self.radius = [16]
        self.elevation = 3
        self.size_hint_y = None
        self.height = dp(80)
        self.md_bg_color = get_color_from_hex("#16213e")
        self.build()

    def build(self):
        from app_cliente.main import ThemeColors

        # Icon box
        icon_box = MDBoxLayout(
            size_hint_x=None,
            width=dp(48),
            padding=dp(4),
        )
        self._icon_label = MDLabel(
            text=self.icon,
            font_style="H4",
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.status_color),
        )
        icon_box.add_widget(self._icon_label)
        self.add_widget(icon_box)

        # Text area
        text_box = MDBoxLayout(orientation="vertical", spacing=dp(2))
        self._title_label = MDLabel(
            text=self.title,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
            size_hint_y=None,
            height=dp(18),
        )
        self._value_label = MDLabel(
            text=self.value,
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(28),
        )
        text_box.add_widget(self._title_label)
        text_box.add_widget(self._value_label)
        self.add_widget(text_box)

    def on_title(self, instance, value):
        if hasattr(self, "_title_label"):
            self._title_label.text = value

    def on_value(self, instance, value):
        if hasattr(self, "_value_label"):
            self._value_label.text = value

    def on_icon(self, instance, value):
        if hasattr(self, "_icon_label"):
            self._icon_label.text = value

    def on_status_color(self, instance, value):
        if hasattr(self, "_icon_label"):
            self._icon_label.text_color = get_color_from_hex(value)

    def pulse_animation(self):
        """Animacao de pulso no cartao."""
        anim = Animation(opacity=0.5, duration=0.4) + Animation(opacity=1.0, duration=0.4)
        anim.start(self)
