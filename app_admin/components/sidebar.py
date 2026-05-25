"""
SideBar — Vertical navigation sidebar for the Flora Admin Panel.

Features:
  - Logo / brand area at top
  - Nav items with icons, labels, active highlight
  - Collapsible (icon-only mode)
  - Smooth transitions
"""

from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    ObjectProperty,
    StringProperty,
)
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView

from app_admin.styles.theme import Colors, Theme


class NavItem(MDFlatButton):
    """Single navigation entry."""

    icon_name = StringProperty("circle")
    item_label = StringProperty("")
    is_active = BooleanProperty(False)

    def __init__(self, screen_name="", on_nav=None, **kwargs):
        self.screen_name = screen_name
        self._on_nav = on_nav
        super().__init__(
            text="",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            md_bg_color=Colors.TRANSPARENT,
            size_hint_y=None,
            height=dp(44),
            radius=[Theme.RADIUS_MEDIUM, 0, 0, Theme.RADIUS_MEDIUM],
            **kwargs,
        )
        self.bind(on_release=self._handle_release)
        self._build()

    def _build(self):
        self._icon = MDIconButton(
            icon=self.icon_name,
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            size_hint_x=None,
            width=dp(44),
        )
        self._label = MDLabel(
            text=self.item_label,
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            font_style="Body2",
        )
        self.add_widget(self._icon)
        self.add_widget(self._label)

    def _handle_release(self, *args):
        if self._on_nav:
            self._on_nav(self.screen_name)

    def set_active(self, active: bool):
        self.is_active = active
        color = Colors.PRIMARY if active else Colors.TEXT_SECONDARY
        self._icon.text_color = color
        self._label.text_color = color
        self.md_bg_color = (
            (*Colors.PRIMARY[:3], 0.1) if active else Colors.TRANSPARENT
        )


class SideBar(MDCard):
    """Sidebar navigation panel."""

    current_screen = StringProperty("dashboard")
    collapsed = BooleanProperty(False)
    on_navigate = ObjectProperty(None)  # callback(screen_name: str)

    NAV_ITEMS = [
        {"icon": "view-dashboard",  "label": "Dashboard",   "screen": "dashboard"},
        {"icon": "robot",           "label": "Bots",        "screen": "bots"},
        {"icon": "account-multiple","label": "Usuários",    "screen": "users"},
        {"icon": "certificate",     "label": "Licenças",    "screen": "licenses"},
        {"icon": "credit-card",     "label": "Planos",      "screen": "plans"},
        {"icon": "chart-bar",       "label": "Analytics",   "screen": "analytics"},
        {"icon": "cog",             "label": "Configurações", "screen": "settings"},
    ]

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_x=None,
            width=Theme.SIDEBAR_WIDTH,
            md_bg_color=Colors.BG_SURFACE,
            radius=[0, Theme.RADIUS_XL, Theme.RADIUS_XL, 0],
            elevation=Theme.ELEVATION_MEDIUM,
            padding=[0, Theme.SPACE_LG, 0, Theme.SPACE_LG],
            spacing=Theme.SPACE_XS,
            **kwargs,
        )
        self._nav_items: dict[str, NavItem] = {}
        self._build()

    def _build(self):
        # ── Brand / Logo ───────────────────────────────────
        brand_box = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            padding=[Theme.SPACE_SM, 0],
            spacing=dp(8),
        )
        logo_icon = MDIconButton(
            icon="flower",
            theme_text_color="Custom",
            text_color=Colors.PRIMARY,
            size_hint_x=None,
            width=dp(40),
        )
        self._brand_label = MDLabel(
            text="Flora Admin",
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        )
        brand_box.add_widget(logo_icon)
        brand_box.add_widget(self._brand_label)
        self.add_widget(brand_box)

        # ── Divider ────────────────────────────────────────
        divider = MDBoxLayout(
            size_hint_y=None,
            height=dp(1),
            md_bg_color=(*Colors.TEXT_HINT[:3], 0.2),
            padding=[Theme.SPACE_SM, 0],
        )
        self.add_widget(divider)

        # ── Scrollable nav items ───────────────────────────
        scroll = MDScrollView(
            do_scroll_x=False,
            bar_width=dp(0),
        )
        self._nav_container = MDBoxLayout(
            orientation="vertical",
            spacing=dp(2),
            size_hint_y=None,
        )
        self._nav_container.bind(
            minimum_height=self._nav_container.setter("height")
        )

        for item in self.NAV_ITEMS:
            nav = NavItem(
                screen_name=item["screen"],
                on_nav=self._on_nav,
            )
            nav.icon_name = item["icon"]
            nav.item_label = item["label"]
            self._nav_items[item["screen"]] = nav
            self._nav_container.add_widget(nav)

        scroll.add_widget(self._nav_container)
        self.add_widget(scroll)

        # ── Collapse toggle (bottom) ───────────────────────
        toggle_btn = MDFlatButton(
            text="",
            icon="menu-open",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_y=None,
            height=dp(36),
            on_release=lambda *a: self.toggle_collapse(),
        )
        self._toggle_btn = toggle_btn
        self.add_widget(toggle_btn)

    def _on_nav(self, screen_name: str):
        self.current_screen = screen_name
        for name, item in self._nav_items.items():
            item.set_active(name == screen_name)
        if self.on_navigate:
            self.on_navigate(screen_name)

    def toggle_collapse(self):
        target_width = Theme.SIDEBAR_COLLAPSED if not self.collapsed else Theme.SIDEBAR_WIDTH
        anim = Animation(width=target_width, duration=Theme.ANIM_MEDIUM)
        anim.start(self)
        self.collapsed = not self.collapsed
        self._toggle_btn.icon = "menu" if self.collapsed else "menu-open"
        self._brand_label.opacity = 0 if self.collapsed else 1
