"""
TopBar — Header bar for the Flora Admin Panel.

Shows:
  - Current page title
  - Admin user name & avatar area
  - Notification bell
  - Logout button
"""

from kivy.metrics import dp
from kivy.properties import StringProperty, ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard

from app_admin.styles.theme import Colors, Theme


class TopBar(MDBoxLayout):
    """Horizontal header bar laid out inside a card."""

    page_title = StringProperty("Dashboard")
    admin_name = StringProperty("Admin")
    on_logout = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=Theme.TOP_BAR_HEIGHT,
            padding=[Theme.SPACE_MD, 0],
            spacing=dp(8),
            **kwargs,
        )
        self._build()

    def _build(self):
        # ── Page title (left) ──────────────────────────────
        self._title_label = MDLabel(
            text=self.page_title,
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=0.5,
            halign="left",
            valign="center",
        )
        self._title_label.bind(size=self._title_label.setter("text_size"))
        self.add_widget(self._title_label)
        self.bind(page_title=lambda *a: setattr(self._title_label, "text", self.page_title))

        # ── Right-side actions ──────────────────────────────
        actions = MDBoxLayout(
            orientation="horizontal",
            size_hint_x=None,
            width=dp(160),
            spacing=dp(4),
            padding=[0, dp(4)],
        )

        # Notification bell
        notif_btn = MDIconButton(
            icon="bell-outline",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            on_release=self._on_notification,
        )
        actions.add_widget(notif_btn)

        # Admin name label
        self._name_label = MDLabel(
            text=self.admin_name,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            halign="center",
            size_hint_x=None,
            width=dp(70),
        )
        self._name_label.bind(size=self._name_label.setter("text_size"))
        actions.add_widget(self._name_label)
        self.bind(admin_name=lambda *a: setattr(self._name_label, "text", self.admin_name))

        # Logout button
        logout_btn = MDIconButton(
            icon="logout",
            theme_text_color="Custom",
            text_color=Colors.HIGHLIGHT,
            on_release=self._on_logout,
        )
        actions.add_widget(logout_btn)

        self.add_widget(actions)

    def _on_notification(self, *args):
        """Placeholder: open notification panel."""
        pass

    def _on_logout(self, *args):
        if self.on_logout:
            self.on_logout()
