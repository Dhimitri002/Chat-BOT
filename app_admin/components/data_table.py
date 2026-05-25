"""
DataTable — A reusable data table widget using KivyMD MDCard + custom rows.

Supports:
  - Column headers
  - Data rows with optional on_select callback
  - Alternating row backgrounds
  - Scrollable body
"""
from kivy.metrics import dp
from kivy.properties import (
    ListProperty,
    ObjectProperty,
    BooleanProperty,
    NumericProperty,
)
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDFlatButton

from app_admin.utils.constants import Colors
from app_admin.styles.theme import Theme


class DataTable(MDCard):
    """Reusable data table with headers and scrollable rows."""

    columns = ListProperty([])  # list of dicts: {"key": str, "header": str, "width": dp}
    data = ListProperty([])     # list of dicts
    on_select = ObjectProperty(None)  # callback(row_data)
    alternate_rows = BooleanProperty(True)
    row_height = NumericProperty(dp(48))
    header_height = NumericProperty(dp(40))

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=dp(0),
            spacing=dp(0),
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_LARGE],
            elevation=Theme.ELEVATION_LOW,
            **kwargs,
        )
        self._build()

    def _build(self):
        # Header row
        self._header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=self.header_height,
            padding=[Theme.SPACE_LG, dp(4)],
            spacing=dp(4),
            md_bg_color=Colors.BG_SURFACE,
        )
        self.add_widget(self._header)

        # Scrollable body
        self._scroll = MDScrollView(
            do_scroll_x=False,
            bar_width=dp(4),
            bar_color=Colors.PRIMARY_LIGHT,
            bar_inactive_color=Colors.BG_INPUT,
        )
        self._body = MDGridLayout(
            cols=1,
            spacing=dp(1),
            size_hint_y=None,
        )
        self._body.bind(minimum_height=self._body.setter("height"))
        self._scroll.add_widget(self._body)
        self.add_widget(self._scroll)

    def _build_headers(self):
        self._header.clear_widgets()
        for col in self.columns:
            w = col.get("width", dp(100))
            lbl = MDLabel(
                text=f"[b]{col.get('header', col['key'])}[/b]",
                markup=True,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
                size_hint_x=None if w else 1,
                width=w if w else None,
                halign="left",
                valign="middle",
            )
            lbl.bind(size=lbl.setter("text_size"))
            self._header.add_widget(lbl)

    def _build_rows(self):
        self._body.clear_widgets()
        for idx, row in enumerate(self.data):
            bg = Colors.BG_CARD if idx % 2 == 0 or not self.alternate_rows else Colors.BG_SURFACE
            row_widget = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=self.row_height,
                padding=[Theme.SPACE_LG, dp(4)],
                spacing=dp(4),
                md_bg_color=bg,
            )
            for col in self.columns:
                w = col.get("width", dp(100))
                val = str(row.get(col["key"], ""))
                cell = MDLabel(
                    text=val,
                    font_style="Body2",
                    theme_text_color="Custom",
                    text_color=Colors.TEXT_PRIMARY,
                    size_hint_x=None if w else 1,
                    width=w if w else None,
                    halign="left",
                    valign="middle",
                    shorten=True,
                    shorten_from="right",
                )
                cell.bind(size=cell.setter("text_size"))
                row_widget.add_widget(cell)

            # Make row clickable
            if self.on_select:
                row_widget.bind(
                    on_touch_down=lambda inst, touch, r=row: (
                        self.on_select(r) if inst.collide_point(*touch.xy) else None
                    )
                )
            self._body.add_widget(row_widget)

    def refresh(self):
        """Rebuild headers and rows from current columns / data."""
        self._build_headers()
        self._build_rows()

    def on_columns(self, _inst, _val):
        self.refresh()

    def on_data(self, _inst, _val):
        self._build_rows()
