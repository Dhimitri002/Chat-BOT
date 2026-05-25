"""
SearchBar — A reusable search input with clear button and filter icon.

Usage:
    search = SearchBar(hint_text="Buscar...")
    search.bind(on_search=lambda text: do_search(text))
"""
from kivy.metrics import dp
from kivy.properties import StringProperty, ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton

from app_admin.utils.constants import Colors
from app_admin.styles.theme import Theme


class SearchBar(MDBoxLayout):
    """Horizontal bar with a text search field and action icons."""

    hint_text = StringProperty("Buscar...")
    text = StringProperty("")
    on_search = ObjectProperty(None)  # callback(text: str)
    on_filter = ObjectProperty(None)  # callback()

    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(4),
            padding=[dp(0), dp(4)],
            **kwargs,
        )
        self._build()

    def _build(self):
        # Search field
        self._field = MDTextField(
            hint_text=self.hint_text,
            mode="round",
            radius=[Theme.RADIUS_MEDIUM],
            fill_color_normal=Colors.BG_INPUT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            icon_left="magnify",
            icon_left_color=Colors.TEXT_HINT,
            size_hint_x=0.85,
            font_size=dp(14),
        )
        self._field.bind(text=self._on_text)
        self.add_widget(self._field)

        # Filter button
        filter_btn = MDIconButton(
            icon="filter-variant",
            icon_size=dp(22),
            theme_icon_color="Custom",
            icon_color=Colors.TEXT_HINT,
            on_release=lambda x: self.on_filter() if self.on_filter else None,
        )
        self.add_widget(filter_btn)

    def _on_text(self, _instance, value):
        self.text = value
        if self.on_search:
            self.on_search(value)

    def on_hint_text(self, _inst, val):
        if hasattr(self, "_field"):
            self._field.hint_text = val

    def clear(self):
        self._field.text = ""
        self.text = ""
