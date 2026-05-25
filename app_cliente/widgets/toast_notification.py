"""Toast Notification - Notificacao toast personalizada."""
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty
from kivy.utils import get_color_from_hex
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout


class ToastNotification(MDCard):
    """Notificacao toast do tipo snackbar."""

    TOP = "top"
    BOTTOM = "bottom"

    def __init__(self, message: str = "", position: str = "bottom",
                 duration: float = 3.0, toast_type: str = "info", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.spacing = dp(8)
        self.padding = dp(16)
        self.radius = [12]
        self.elevation = 6
        self.size_hint = (0.9, None)
        self.height = dp(48)
        self.pos_hint = {"center_x": 0.5}

        self._duration = duration

        from app_cliente.main import ThemeColors

        type_colors = {
            "info": ThemeColors.ACCENT,
            "success": ThemeColors.SUCCESS,
            "warning": ThemeColors.WARNING,
            "error": ThemeColors.ERROR,
        }
        bg_color = type_colors.get(toast_type, ThemeColors.ACCENT)
        self.md_bg_color = get_color_from_hex(bg_color)

        # Icon
        icons = {"info": "information", "success": "check-circle",
                 "warning": "alert", "error": "alert-circle"}
        icon = icons.get(toast_type, "information")
        self._icon = MDLabel(
            text=icon, size_hint_x=None, width=dp(30),
            font_style="H6", halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
        )
        self.add_widget(self._icon)

        # Message
        self._msg_label = MDLabel(
            text=message,
            font_style="Body2",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
        )
        self.add_widget(self._msg_label)

        # Start animation
        self.opacity = 0

    def show(self):
        """Exibe a notificacao."""
        anim = Animation(opacity=1, duration=0.3)
        anim.start(self)
        Clock.schedule_once(self.dismiss, self._duration)

    def dismiss(self, *args):
        """Esconde e remove a notificacao."""
        from kivy.app import App
        try:
            parent = self.parent
        except ReferenceError:
            parent = None

        anim = Animation(opacity=0, duration=0.3)
        if parent:
            anim.bind(on_complete=lambda *a: parent.remove_widget(self))
        anim.start(self)
