"""
Flora Client App — Premium Reusable Components (Warm Edition)
==============================================================
Friendly, cute-leaning components with warm dark theme.
Perfect for a WhatsApp chatbot management app.

Components:
  - PremiumCard: Soft rounded card with warm surface
  - GradientButton: Friendly gradient button
  - StatusBadge: Cute status pill
  - SearchBar: Rounded search input
  - StatCard: Metric card
  - ChatBubble: Chat message bubble (user vs Flora)
  - TypingIndicator: Animated typing dots
  - EmptyState: Friendly empty state
  - ModalDialog: Soft modal dialog
  - SkeletonLoader: Loading placeholder
  - BottomNavBar: Material bottom navigation
  - SnackbarNotification: Toast notifications
  - ProgressBar: Styled progress bar
  - Divider: Styled divider
"""

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty, ColorProperty, ListProperty,
    NumericProperty, ObjectProperty, OptionProperty,
    StringProperty,
)
from kivy.uix.boxlayout import MDBoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget

from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel as KivyMDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout as KivyMDBoxLayout
from kivymd.uix.scrollview import MDScrollView

from app_cliente.styles.theme import (
    Colors, Typography, Spacing, Radius,
    Elevation, Animation as AnimTiming, ComponentTokens,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  PREMIUM CARD (Warm Edition)
# ═══════════════════════════════════════════════════════════════════════════════

class PremiumCard(MDCard):
    """
    Premium card with softer, warmer appearance.
    Slightly more rounded than admin version.
    """

    hover_enabled = BooleanProperty(False)
    hover_elevation = NumericProperty(Elevation.MEDIUM)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elevation = Elevation.LOW
        self.radius = [Radius.LG]
        self.md_bg_color = Colors.BG_CARD
        self.padding = ComponentTokens.CARD_PADDING
        self.spacing = ComponentTokens.CARD_SPACING
        self.size_hint_y = None
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(self._update_canvas, 0)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*Colors.BG_CARD)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[Radius.LG],
            )
            Color(*ComponentTokens.CARD_BORDER_COLOR)
            Line(
                rounded_rectangle=(
                    self.x, self.y, self.width, self.height, Radius.LG
                ),
                width=ComponentTokens.CARD_BORDER_WIDTH,
            )


# ═══════════════════════════════════════════════════════════════════════════════
#  GRADIENT BUTTON (Warm Edition)
# ═══════════════════════════════════════════════════════════════════════════════

class GradientButton(MDRaisedButton):
    """Friendly gradient button with warm colors."""

    gradient_colors = ListProperty(Colors.GRADIENT_PRIMARY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = Colors.PRIMARY
        self.text_color = Colors.TEXT_ON_ACCENT
        self.font_size = Typography.BUTTON
        self.bold = True
        self.elevation = Elevation.LOW
        self.radius = [ComponentTokens.BUTTON_RADIUS]
        self.size_hint_y = None
        self.height = ComponentTokens.BUTTON_HEIGHT
        self.padding = [ComponentTokens.BUTTON_PADDING_H, 0]
        self.theme_text_color = "Custom"

    def on_press(self):
        Animation(elevation=Elevation.NONE, d=AnimTiming.FAST).start(self)

    def on_release(self):
        Animation(elevation=Elevation.LOW, d=AnimTiming.FAST).start(self)


# ═══════════════════════════════════════════════════════════════════════════════
#  STATUS BADGE (Cute Edition)
# ═══════════════════════════════════════════════════════════════════════════════

class StatusBadge(MDBoxLayout):
    """Cute colored pill badge for status display."""

    status = OptionProperty("default", options=[
        "connected", "disconnected", "pending", "error",
        "active", "inactive", "default",
    ])
    text = StringProperty("")

    STATUS_COLORS = {
        "connected":    Colors.STATUS_CONNECTED,
        "disconnected": Colors.STATUS_DISCONNECTED,
        "pending":      Colors.STATUS_PENDING,
        "error":        Colors.STATUS_ERROR,
        "active":       Colors.STATUS_ACTIVE,
        "inactive":     Colors.STATUS_INACTIVE,
        "default":      Colors.TEXT_HINT,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.height = ComponentTokens.BADGE_HEIGHT
        self.padding = [ComponentTokens.BADGE_PADDING_H, Spacing.XS]
        self.spacing = Spacing.XS
        self._build()

    def _build(self):
        self.clear_widgets()
        color = self.STATUS_COLORS.get(self.status, Colors.TEXT_HINT)

        # Dot
        dot = Widget(size_hint=(None, None), size=(dp(6), dp(6)))
        dot.pos_hint = {"center_y": 0.5}
        with dot.canvas.before:
            Color(*color)
            Ellipse(pos=dot.pos, size=dot.size)
        self.add_widget(dot)

        # Label
        label = KivyMDLabel(
            text=self.text or self.status.capitalize(),
            font_style=Typography.CAPTION_STYLE,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=None,
            halign="center",
        )
        label.bind(texture_size=label.setter("size"))
        self.add_widget(label)
        Clock.schedule_once(self._update_size, 0)

    def _update_size(self, *args):
        if len(self.children) >= 2:
            self.width = (
                self.children[-1].width + Spacing.XS +
                self.children[-2].width + ComponentTokens.BADGE_PADDING_H * 2
            )


# ═══════════════════════════════════════════════════════════════════════════════
#  CHAT BUBBLE
# ═══════════════════════════════════════════════════════════════════════════════

class ChatBubble(MDBoxLayout):
    """
    Chat message bubble for Flora chat screen.

    Usage:
        ChatBubble:
            text: "Olá! Como posso ajudar?"
            is_user: False  # Flora message
    """

    text = StringProperty("")
    is_user = BooleanProperty(False)
    timestamp = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(2)
        self.padding = [ComponentTokens.BUBBLE_PADDING_H, ComponentTokens.BUBBLE_PADDING_V]
        self.size_hint_y = None
        self.size_hint_x = None
        self.width = dp(280)
        self._build()
        self.bind(text=self._update)

    def _build(self):
        self.clear_widgets()

        bg_color = Colors.PRIMARY if self.is_user else Colors.BG_INPUT
        radius_val = ComponentTokens.BUBBLE_RADIUS
        align = "right" if self.is_user else "left"

        # Bubble card
        bubble = MDCard(
            padding=self.padding,
            radius=[
                radius_val, radius_val,
                radius_val if self.is_user else dp(4),
                dp(4) if self.is_user else radius_val,
            ],
            md_bg_color=bg_color,
            elevation=Elevation.NONE,
            size_hint_y=None,
            size_hint_x=None,
            width=min(self.width, dp(280)),
            halign=align,
        )

        text_label = KivyMDLabel(
            text=self.text,
            font_style=Typography.BODY1,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY if self.is_user else Colors.TEXT_PRIMARY,
            size_hint_y=None,
            text_size=(bubble.width - dp(28), None),
            halign="left",
        )
        text_label.bind(texture_size=text_label.setter("size"))
        bubble.add_widget(text_label)
        bubble.height = text_label.height + ComponentTokens.BUBBLE_PADDING_V * 2

        self.add_widget(bubble)

        # Timestamp
        if self.timestamp:
            ts = KivyMDLabel(
                text=self.timestamp,
                font_style=Typography.CAPTION_STYLE,
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                halign=align,
                size_hint_y=None,
                height=dp(16),
            )
            self.add_widget(ts)

        self.height = bubble.height + (dp(16) if self.timestamp else 0)

    def _update(self, *args):
        self._build()


# ═══════════════════════════════════════════════════════════════════════════════
#  TYPING INDICATOR
# ═══════════════════════════════════════════════════════════════════════════════

class TypingIndicator(MDBoxLayout):
    """Animated typing indicator (three bouncing dots)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.spacing = dp(4)
        self.size_hint_y = None
        self.height = dp(36)
        self.padding = [ComponentTokens.BUBBLE_PADDING_H, ComponentTokens.BUBBLE_PADDING_V]
        self._dots = []
        self._build()

    def _build(self):
        self.clear_widgets()
        for i in range(3):
            dot = Widget(size_hint=(None, None), size=(dp(8), dp(8)))
            self._dots.append(dot)
            self.add_widget(dot)

        self._animate_dots()

    def _animate_dots(self):
        for i, dot in enumerate(self._dots):
            delay = i * 0.2
            anim = Animation(
                opacity=0.3,
                d=AnimTiming.SLOW,
                t="in_out_cubic",
            ) + Animation(
                opacity=1.0,
                d=AnimTiming.SLOW,
                t="in_out_cubic",
            )
            anim.repeat = True
            Clock.schedule_once(lambda dt, a=anim, d=dot: a.start(d), delay)

    def on_pos(self, *args):
        for dot in self._dots:
            with dot.canvas.before:
                dot.canvas.before.clear()
                Color(*Colors.TEXT_HINT)
                Ellipse(pos=(dot.center_x - dp(4), dot.center_y - dp(4)), size=(dp(8), dp(8)))


# ═══════════════════════════════════════════════════════════════════════════════
#  SEARCH BAR (Warm Edition)
# ═══════════════════════════════════════════════════════════════════════════════

class SearchBar(MDBoxLayout):
    """Rounded search bar for client app."""

    hint_text = StringProperty("Buscar...")
    text = StringProperty("")
    search_callback = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = ComponentTokens.INPUT_HEIGHT
        self.spacing = Spacing.SM
        self.padding = [Spacing.SM, 0]
        self._build()

    def _build(self):
        self.clear_widgets()
        self.add_widget(MDIconButton(
            icon="magnify",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_x=None,
            width=dp(40),
        ))
        self._field = MDTextField(
            hint_text=self.hint_text,
            mode="round",
            text=self.text,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            radius=[ComponentTokens.INPUT_RADIUS],
        )
        self._field.bind(text=self._on_text)
        self.add_widget(self._field)

    def _on_text(self, instance, value):
        self.text = value
        if self.search_callback:
            self.search_callback(value)


# ═══════════════════════════════════════════════════════════════════════════════
#  STAT CARD (Warm Edition)
# ═══════════════════════════════════════════════════════════════════════════════

class StatCard(MDCard):
    """Metric card with warm styling."""

    title = StringProperty("")
    value = StringProperty("0")
    subtitle = StringProperty("")
    icon = StringProperty("chart-line")
    accent_color = ColorProperty(Colors.PRIMARY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.padding = ComponentTokens.CARD_PADDING
        self.spacing = Spacing.MD
        self.md_bg_color = Colors.BG_CARD
        self.radius = [ComponentTokens.BUTTON_RADIUS]
        self.elevation = Elevation.LOW
        self.size_hint_y = None
        self.height = dp(96)

        self._icon_btn = MDIconButton(
            icon=self.icon,
            theme_text_color="Custom",
            text_color=self.accent_color,
            user_font_size=dp(28),
            size_hint_x=None,
            width=dp(52),
        )
        self.add_widget(self._icon_btn)

        text_box = KivyMDBoxLayout(orientation="vertical", spacing=dp(2))
        text_box.add_widget(KivyMDLabel(
            text=self.title,
            font_style=Typography.CAPTION_STYLE,
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
        ))
        text_box.add_widget(KivyMDLabel(
            text=self.value,
            font_style=Typography.H4,
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        ))
        text_box.add_widget(KivyMDLabel(
            text=self.subtitle,
            font_style=Typography.CAPTION_STYLE,
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
        ))
        self.add_widget(text_box)


# ═══════════════════════════════════════════════════════════════════════════════
#  EMPTY STATE (Friendly Edition)
# ═══════════════════════════════════════════════════════════════════════════════

class EmptyState(MDBoxLayout):
    """Friendly empty state with cute messaging."""

    icon = StringProperty("robot-happy")
    title = StringProperty("Nada aqui ainda")
    description = StringProperty("Vamos comecar?")
    icon_color = ColorProperty(Colors.TEXT_HINT)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = Spacing.MD
        self.padding = Spacing.XL
        self.size_hint_y = None
        self.height = dp(240)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self._build()

    def _build(self):
        self.clear_widgets()
        self.add_widget(MDIconButton(
            icon=self.icon,
            theme_text_color="Custom",
            text_color=self.icon_color,
            user_font_size=dp(64),
            size_hint_y=None,
            height=dp(80),
            pos_hint={"center_x": 0.5},
        ))
        self.add_widget(KivyMDLabel(
            text=self.title,
            font_style=Typography.H6,
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            halign="center",
            size_hint_y=None,
            height=dp(32),
        ))
        self.add_widget(KivyMDLabel(
            text=self.description,
            font_style=Typography.BODY2,
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            halign="center",
            size_hint_y=None,
            height=dp(48),
        ))


# ═══════════════════════════════════════════════════════════════════════════════
#  MODAL DIALOG (Warm Edition)
# ═══════════════════════════════════════════════════════════════════════════════

class ModalDialog(MDDialog):
    """Soft modal dialog with warm styling."""

    def __init__(self, title="", text="", on_confirm=None, on_cancel=None, **kwargs):
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel

        buttons = [
            MDFlatButton(
                text="CANCELAR",
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
                on_release=self._handle_cancel,
            ),
            MDRaisedButton(
                text="CONFIRMAR",
                md_bg_color=Colors.PRIMARY,
                text_color=Colors.TEXT_ON_ACCENT,
                theme_text_color="Custom",
                on_release=self._handle_confirm,
            ),
        ]

        super().__init__(
            title=title,
            text=text,
            buttons=buttons,
            radius=[ComponentTokens.MODAL_RADIUS],
            md_bg_color=Colors.BG_CARD,
            size_hint=(None, None),
            width=ComponentTokens.MODAL_WIDTH,
        )

    def _handle_confirm(self, *args):
        self.dismiss()
        if self._on_confirm:
            self._on_confirm()

    def _handle_cancel(self, *args):
        self.dismiss()
        if self._on_cancel:
            self._on_cancel()


# ═══════════════════════════════════════════════════════════════════════════════
#  SKELETON LOADER (Warm Edition)
# ═══════════════════════════════════════════════════════════════════════════════

class SkeletonLoader(MDBoxLayout):
    """Loading placeholder with shimmer animation."""

    count = NumericProperty(3)
    row_height = NumericProperty(dp(48))
    spacing = NumericProperty(dp(6))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = self.spacing
        self.size_hint_y = None
        self.height = self.count * (self.row_height + self.spacing)
        self._build()

    def _build(self):
        self.clear_widgets()
        for _ in range(self.count):
            row = MDCard(
                size_hint_y=None,
                height=self.row_height,
                md_bg_color=Colors.BG_INPUT,
                radius=[Radius.SM],
                elevation=Elevation.NONE,
            )
            self.add_widget(row)
            anim = Animation(opacity=0.4, d=AnimTiming.SLOW, t="in_out_cubic") + \
                   Animation(opacity=1.0, d=AnimTiming.SLOW, t="in_out_cubic")
            anim.repeat = True
            anim.start(row)


# ═══════════════════════════════════════════════════════════════════════════════
#  SNACKBAR NOTIFICATION (Warm Edition)
# ═══════════════════════════════════════════════════════════════════════════════

class SnackbarNotification(MDCard):
    """Toast notification with warm styling."""

    TYPES = {
        "success": (Colors.SUCCESS, "check-circle"),
        "error":   (Colors.ERROR, "alert-circle"),
        "warning": (Colors.WARNING, "alert"),
        "info":    (Colors.INFO, "information"),
    }

    @staticmethod
    def show(parent, message: str, snackbar_type: str = "info", duration: float = 3.0):
        color, icon = SnackbarNotification.TYPES.get(
            snackbar_type, (Colors.INFO, "information")
        )

        snackbar = MDCard(
            orientation="horizontal",
            padding=ComponentTokens.SNACKBAR_PADDING,
            spacing=Spacing.SM,
            md_bg_color=Colors.BG_CARD,
            radius=[ComponentTokens.SNACKBAR_RADIUS],
            elevation=Elevation.HIGH,
            size_hint=(None, None),
            height=dp(52),
            width=min(dp(400), parent.width - dp(32)),
            pos_hint={"center_x": 0.5},
            y=-dp(60),
            opacity=0,
        )

        snackbar.add_widget(MDIconButton(
            icon=icon,
            theme_text_color="Custom",
            text_color=color,
            size_hint_x=None,
            width=dp(40),
        ))
        snackbar.add_widget(KivyMDLabel(
            text=message,
            font_style=Typography.BODY2,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        ))

        parent.add_widget(snackbar)

        Animation(
            y=ComponentTokens.SNACKBAR_MARGIN,
            opacity=1,
            d=AnimTiming.NORMAL,
            t="out_cubic",
        ).start(snackbar)

        def _dismiss(dt):
            anim = Animation(y=-dp(60), opacity=0, d=AnimTiming.NORMAL, t="in_cubic")
            anim.bind(on_complete=lambda *a: parent.remove_widget(snackbar))
            anim.start(snackbar)

        Clock.schedule_once(_dismiss, duration)


# ═══════════════════════════════════════════════════════════════════════════════
#  PROGRESS BAR (Warm Edition)
# ═══════════════════════════════════════════════════════════════════════════════

class ProgressBar(MDBoxLayout):
    """Styled progress bar."""

    value = NumericProperty(0)
    bar_color = ColorProperty(Colors.PRIMARY)
    bg_color = ColorProperty(Colors.BG_INPUT)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(6)
        self.bind(pos=self._draw, size=self._draw, value=self._draw)
        Clock.schedule_once(self._draw, 0)

    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(3)])
            fill_width = max(0, (self.value / 100.0) * self.width)
            if fill_width > 0:
                Color(*self.bar_color)
                RoundedRectangle(
                    pos=self.pos, size=(fill_width, self.height), radius=[dp(3)]
                )


# ═══════════════════════════════════════════════════════════════════════════════
#  DIVIDER (Warm Edition)
# ═══════════════════════════════════════════════════════════════════════════════

class Divider(MDBoxLayout):
    """Styled divider."""

    divider_color = ColorProperty(ComponentTokens.CARD_BORDER_COLOR)
    thickness = NumericProperty(dp(1))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = self.thickness
        self.bind(pos=self._draw, size=self._draw)
        Clock.schedule_once(self._draw, 0)

    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.divider_color)
            RoundedRectangle(pos=self.pos, size=self.size)
