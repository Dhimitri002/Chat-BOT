"""
Flora Admin Panel — Premium Reusable Components
================================================
Beautiful, production-ready UI components with dark theme,
smooth animations, and consistent design language.

Components:
  - PremiumCard: Rounded card with subtle shadow and hover effect
  - GradientButton: Button with gradient background and ripple
  - StatusBadge: Colored pill badge for status display
  - SearchBar: Modern search input with icon
  - StatCard: Dashboard metric card with icon and value
  - DataTable: Styled table with hover rows
  - ModalDialog: Beautiful modal overlay
  - AnimatedFAB: Floating action button with animation
  - SnackbarNotification: Toast-style notifications
  - SkeletonLoader: Loading placeholder animation
  - EmptyState: Empty state with illustration
  - IconButton: Styled icon button
  - Divider: Styled divider/separator
  - ProgressBar: Styled progress indicator
  - Tooltip: Hover tooltip
"""

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty, ColorProperty, ListProperty,
    NumericProperty, ObjectProperty, OptionProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import MDBoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import MDLabel
from kivy.uix.widget import Widget

from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel as KivyMDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout as KivyMDBoxLayout
from kivymd.uix.scrollview import MDScrollView

from app_admin.styles.theme import (
    Colors, Typography, Spacing, Radius,
    Elevation, Animation as AnimTiming, ComponentTokens,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  PREMIUM CARD
# ═══════════════════════════════════════════════════════════════════════════════

class PremiumCard(MDCard):
    """
    Premium card with subtle shadow, border, and optional hover effect.

    Usage:
        PremiumCard:
            md_bg_color: app.theme_cls.bg_card
            radius: [16]
    """

    hover_enabled = BooleanProperty(False)
    hover_elevation = NumericProperty(Elevation.MEDIUM)
    border_color = ColorProperty(ComponentTokens.CARD_BORDER_COLOR)
    border_width = NumericProperty(ComponentTokens.CARD_BORDER_WIDTH)

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
            # Subtle border
            Color(*ComponentTokens.CARD_BORDER_COLOR)
            Line(
                rounded_rectangle=(
                    self.x, self.y, self.width, self.height, Radius.LG
                ),
                width=ComponentTokens.CARD_BORDER_WIDTH,
            )

    def on_hover_enabled(self, instance, value):
        if value:
            self.bind(on_enter=self._on_hover_enter, on_leave=self._on_hover_leave)

    def _on_hover_enter(self, *args):
        if self.hover_enabled:
            Animation(
                elevation=self.hover_elevation,
                d=AnimTiming.FAST,
                t="out_cubic",
            ).start(self)

    def _on_hover_leave(self, *args):
        if self.hover_enabled:
            Animation(
                elevation=Elevation.LOW,
                d=AnimTiming.FAST,
                t="out_cubic",
            ).start(self)


# ═══════════════════════════════════════════════════════════════════════════════
#  GRADIENT BUTTON
# ═══════════════════════════════════════════════════════════════════════════════

class GradientButton(MDRaisedButton):
    """
    Premium button with gradient-like appearance and ripple effect.

    Usage:
        GradientButton:
            text: "Salvar"
            gradient_colors: app.theme_cls.gradient_primary
    """

    gradient_colors = ListProperty(Colors.GRADIENT_PRIMARY)
    button_radius = NumericProperty(Radius.MD)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = Colors.PRIMARY
        self.text_color = Colors.TEXT_ON_ACCENT
        self.font_size = Typography.BUTTON
        self.bold = True
        self.elevation = Elevation.LOW
        self.radius = [self.button_radius]
        self.size_hint_y = None
        self.height = ComponentTokens.BUTTON_HEIGHT
        self.padding = [ComponentTokens.BUTTON_PADDING_H, 0]
        self.theme_text_color = "Custom"

    def on_press(self):
        """Press animation."""
        Animation(
            elevation=Elevation.NONE,
            d=AnimTiming.FAST,
        ).start(self)

    def on_release(self):
        """Release animation."""
        Animation(
            elevation=Elevation.LOW,
            d=AnimTiming.FAST,
        ).start(self)


class GradientIconButton(MDIconButton):
    """Icon button with accent color and ripple."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_text_color = "Custom"
        self.text_color = Colors.PRIMARY
        self.icon_color = Colors.PRIMARY


# ═══════════════════════════════════════════════════════════════════════════════
#  STATUS BADGE
# ═══════════════════════════════════════════════════════════════════════════════

class StatusBadge(MDBoxLayout):
    """
    Colored pill badge for status display.

    Usage:
        StatusBadge:
            status: "connected"  # or "disconnected", "pending", "error"
    """

    status = OptionProperty("default", options=[
        "connected", "disconnected", "pending", "error",
        "active", "inactive", "default",
    ])
    text = StringProperty("")
    badge_radius = NumericProperty(Radius.FULL)

    # Status-to-color mapping
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
        self.pos_hint = {"center_y": 0.5}
        self._build()
        self.bind(status=self._update_color, text=self._update_text)

    def _build(self):
        self.clear_widgets()
        # Dot indicator
        self._dot = Widget(size_hint=(None, None), size=(dp(6), dp(6)))
        self._dot.pos_hint = {"center_y": 0.5}
        self._update_dot_color()
        self.add_widget(self._dot)

        # Label
        self._label = KivyMDLabel(
            text=self.text or self.status.capitalize(),
            font_style=Typography.CAPTION_STYLE,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=None,
            halign="center",
            shorten=True,
        )
        self._label.bind(texture_size=self._label.setter("size"))
        self.add_widget(self._label)

        # Set width after widgets are added
        Clock.schedule_once(self._update_size, 0)

    def _update_dot_color(self):
        color = self.STATUS_COLORS.get(self.status, Colors.TEXT_HINT)
        self._dot.canvas.before.clear()
        with self._dot.canvas.before:
            Color(*color)
            RoundedRectangle(
                pos=self._dot.pos,
                size=self._dot.size,
                radius=[dp(3)],
            )

    def _update_color(self, *args):
        self._update_dot_color()
        self._update_size()

    def _update_text(self, *args):
        if self._label:
            self._label.text = self.text or self.status.capitalize()
        self._update_size()

    def _update_size(self, *args):
        if hasattr(self, '_label') and hasattr(self, '_dot'):
            total_width = self._dot.width + Spacing.XS + max(self._label.width, dp(40)) + ComponentTokens.BADGE_PADDING_H * 2
            self.width = total_width


# ═══════════════════════════════════════════════════════════════════════════════
#  SEARCH BAR
# ═══════════════════════════════════════════════════════════════════════════════

class SearchBar(MDBoxLayout):
    """
    Modern search input with icon and clear button.

    Usage:
        SearchBar:
            hint_text: "Buscar..."
            on_search: app.do_search(self.text)
    """

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

        # Search icon
        icon = MDIconButton(
            icon="magnify",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_x=None,
            width=dp(40),
        )
        self.add_widget(icon)

        # Text field
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
            radius=[Radius.MD],
        )
        self._field.bind(text=self._on_text_changed)
        self.add_widget(self._field)

        # Clear button (hidden by default)
        self._clear_btn = MDIconButton(
            icon="close-circle",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_x=None,
            width=dp(40),
            opacity=0,
            on_release=self._clear,
        )
        self.add_widget(self._clear_btn)

    def _on_text_changed(self, instance, value):
        self.text = value
        self._clear_btn.opacity = 1 if value else 0
        if self.search_callback:
            self.search_callback(value)

    def _clear(self, *args):
        self._field.text = ""
        self.text = ""


# ═══════════════════════════════════════════════════════════════════════════════
#  STAT CARD
# ═══════════════════════════════════════════════════════════════════════════════

class StatCard(MDCard):
    """
    Dashboard metric card with icon, value, and subtitle.

    Usage:
        StatCard:
            title: "Mensagens"
            value: "1,234"
            subtitle: "128 hoje"
            icon: "message-text"
            accent_color: app.theme_cls.primary
    """

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
        self.radius = [Radius.LG]
        self.elevation = Elevation.LOW
        self.size_hint_y = None
        self.height = dp(96)
        self._build()
        self.bind(
            title=self._update_title,
            value=self._update_value,
            subtitle=self._update_subtitle,
            icon=self._update_icon,
            accent_color=self._update_accent,
        )

    def _build(self):
        self.clear_widgets()

        # Icon
        self._icon_btn = MDIconButton(
            icon=self.icon,
            theme_text_color="Custom",
            text_color=self.accent_color,
            user_font_size=dp(28),
            size_hint_x=None,
            width=dp(52),
        )
        self.add_widget(self._icon_btn)

        # Text content
        self._text_box = KivyMDBoxLayout(orientation="vertical", spacing=dp(2))
        self._title_lbl = KivyMDLabel(
            text=self.title,
            font_style=Typography.CAPTION_STYLE,
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
        )
        self._value_lbl = KivyMDLabel(
            text=self.value,
            font_style=Typography.H4,
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        )
        self._subtitle_lbl = KivyMDLabel(
            text=self.subtitle,
            font_style=Typography.CAPTION_STYLE,
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
        )
        self._text_box.add_widget(self._title_lbl)
        self._text_box.add_widget(self._value_lbl)
        self._text_box.add_widget(self._subtitle_lbl)
        self.add_widget(self._text_box)

    def _update_title(self, *args):
        if hasattr(self, '_title_lbl'):
            self._title_lbl.text = self.title

    def _update_value(self, *args):
        if hasattr(self, '_value_lbl'):
            self._value_lbl.text = self.value

    def _update_subtitle(self, *args):
        if hasattr(self, '_subtitle_lbl'):
            self._subtitle_lbl.text = self.subtitle

    def _update_icon(self, *args):
        if hasattr(self, '_icon_btn'):
            self._icon_btn.icon = self.icon

    def _update_accent(self, *args):
        if hasattr(self, '_icon_btn'):
            self._icon_btn.text_color = self.accent_color


# ═══════════════════════════════════════════════════════════════════════════════
#  DATA TABLE
# ═══════════════════════════════════════════════════════════════════════════════

class DataTable(MDBoxLayout):
    """
    Styled data table with header, hover rows, and scroll.

    Usage:
        DataTable:
            columns: ["Nome", "Email", "Status"]
            rows: [["João", "joao@email.com", "Ativo"], ...]
    """

    columns = ListProperty([])
    rows = ListProperty([])
    header_bg = ColorProperty(Colors.BG_SECONDARY)
    row_hover_bg = ColorProperty(Colors.BG_HOVER)
    border_color = ColorProperty(ComponentTokens.CARD_BORDER_COLOR)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 0
        self.size_hint_y = None
        self.bind(columns=self._rebuild, rows=self._rebuild)
        Clock.schedule_once(lambda dt: self._rebuild(), 0)

    def _rebuild(self, *args):
        self.clear_widgets()
        self.height = 0

        if not self.columns:
            return

        # Header row
        header = KivyMDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            padding=[Spacing.MD, 0],
            md_bg_color=self.header_bg,
        )
        for col in self.columns:
            lbl = KivyMDLabel(
                text=col,
                font_style=Typography.BUTTON_STYLE,
                bold=True,
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
                size_hint_x=1,
                shorten=True,
            )
            header.add_widget(lbl)
        self.add_widget(header)
        self.height += header.height

        # Data rows
        for i, row in enumerate(self.rows):
            row_bg = Colors.BG_CARD if i % 2 == 0 else Colors.BG_SECONDARY
            row_widget = KivyMDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(48),
                padding=[Spacing.MD, 0],
                md_bg_color=row_bg,
            )
            for cell in row:
                lbl = KivyMDLabel(
                    text=str(cell),
                    font_style=Typography.BODY2,
                    theme_text_color="Custom",
                    text_color=Colors.TEXT_PRIMARY,
                    size_hint_x=1,
                    shorten=True,
                )
                row_widget.add_widget(lbl)
            self.add_widget(row_widget)
            self.height += row_widget.height


# ═══════════════════════════════════════════════════════════════════════════════
#  MODAL DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class ModalDialog(MDDialog):
    """
    Beautiful modal overlay with premium styling.

    Usage:
        modal = ModalDialog(
            title="Confirmar",
            text="Tem certeza que deseja excluir?",
            on_confirm=app.delete_item,
        )
        modal.open()
    """

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
            radius=[Radius.XL],
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
#  ANIMATED FAB
# ═══════════════════════════════════════════════════════════════════════════════

class AnimatedFAB(MDRaisedButton):
    """
    Floating action button with entrance animation and pulse.

    Usage:
        AnimatedFAB:
            icon: "plus"
            on_release: app.add_new()
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.icon = "plus"
        self.md_bg_color = Colors.PRIMARY
        self.text_color = Colors.TEXT_ON_ACCENT
        self.font_size = dp(24)
        self.elevation = Elevation.MEDIUM
        self.radius = [Radius.XL]
        self.size_hint = (None, None)
        self.size = (ComponentTokens.FAB_SIZE, ComponentTokens.FAB_SIZE)
        self.pos_hint = {"right": 0.96, "y": 0.04}
        self.theme_text_color = "Custom"
        self.opacity = 0
        self._scale = 0

    def show(self, *args):
        """Animate FAB entrance."""
        self.opacity = 1
        Animation(
            scale=1,
            d=AnimTiming.NORMAL,
            t="out_back",
        ).start(self)

    def hide(self, *args):
        """Animate FAB exit."""
        anim = Animation(
            scale=0,
            d=AnimTiming.FAST,
            t="in_cubic",
        )
        anim.bind(on_complete=lambda *a: setattr(self, "opacity", 0))
        anim.start(self)

    def on_enter(self, *args):
        """Pulse animation on hover."""
        Animation(
            scale=1.1,
            d=AnimTiming.FAST,
            t="out_cubic",
        ).start(self)

    def on_leave(self, *args):
        """Return to normal size."""
        Animation(
            scale=1.0,
            d=AnimTiming.FAST,
            t="out_cubic",
        ).start(self)


# ═══════════════════════════════════════════════════════════════════════════════
#  SNACKBAR NOTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

class SnackbarNotification(MDCard):
    """
    Toast-style notification that slides in from the bottom.

    Usage:
        SnackbarNotification.show(
            parent=root,
            message="Item salvo com sucesso!",
            type="success"
        )
    """

    TYPES = {
        "success": (Colors.SUCCESS, "check-circle"),
        "error":   (Colors.ERROR, "alert-circle"),
        "warning": (Colors.WARNING, "alert"),
        "info":    (Colors.INFO, "information"),
    }

    @staticmethod
    def show(parent, message: str, snackbar_type: str = "info", duration: float = 3.0):
        """Show a snackbar notification."""
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

        # Border accent
        with snackbar.canvas.before:
            Color(*color)
            Line(
                rounded_rectangle=(
                    snackbar.x, snackbar.y,
                    snackbar.width, snackbar.height,
                    ComponentTokens.SNACKBAR_RADIUS,
                ),
                width=dp(1.5),
            )

        icon_btn = MDIconButton(
            icon=icon,
            theme_text_color="Custom",
            text_color=color,
            size_hint_x=None,
            width=dp(40),
        )
        snackbar.add_widget(icon_btn)

        label = KivyMDLabel(
            text=message,
            font_style=Typography.BODY2,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        )
        snackbar.add_widget(label)

        parent.add_widget(snackbar)

        # Slide in
        Animation(
            y=ComponentTokens.SNACKBAR_MARGIN,
            opacity=1,
            d=AnimTiming.NORMAL,
            t="out_cubic",
        ).start(snackbar)

        # Auto-dismiss
        def _dismiss(dt):
            anim = Animation(
                y=-dp(60),
                opacity=0,
                d=AnimTiming.NORMAL,
                t="in_cubic",
            )
            anim.bind(on_complete=lambda *a: parent.remove_widget(snackbar))
            anim.start(snackbar)

        Clock.schedule_once(_dismiss, duration)


# ═══════════════════════════════════════════════════════════════════════════════
#  SKELETON LOADER
# ═══════════════════════════════════════════════════════════════════════════════

class SkeletonLoader(MDBoxLayout):
    """
    Loading placeholder with shimmer animation.

    Usage:
        SkeletonLoader:
            count: 3  # Number of skeleton rows
    """

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
            # Animate opacity for shimmer
            anim = Animation(
                opacity=0.4,
                d=AnimTiming.SLOW,
                t="in_out_cubic",
            ) + Animation(
                opacity=1.0,
                d=AnimTiming.SLOW,
                t="in_out_cubic",
            )
            anim.repeat = True
            anim.start(row)


# ═══════════════════════════════════════════════════════════════════════════════
#  EMPTY STATE
# ═══════════════════════════════════════════════════════════════════════════════

class EmptyState(MDBoxLayout):
    """
    Empty state with icon, title, and description.

    Usage:
        EmptyState:
            icon: "robot-off"
            title: "Nenhum bot encontrado"
            description: "Crie seu primeiro bot para começar"
    """

    icon = StringProperty("package-variant")
    title = StringProperty("Nada aqui ainda")
    description = StringProperty("Comece adicionando um novo item")
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

        icon = MDIconButton(
            icon=self.icon,
            theme_text_color="Custom",
            text_color=self.icon_color,
            user_font_size=dp(64),
            size_hint_y=None,
            height=dp(80),
            pos_hint={"center_x": 0.5},
        )
        self.add_widget(icon)

        title = KivyMDLabel(
            text=self.title,
            font_style=Typography.H6,
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            halign="center",
            size_hint_y=None,
            height=dp(32),
        )
        self.add_widget(title)

        desc = KivyMDLabel(
            text=self.description,
            font_style=Typography.BODY2,
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            halign="center",
            size_hint_y=None,
            height=dp(48),
        )
        self.add_widget(desc)


# ═══════════════════════════════════════════════════════════════════════════════
#  PROGRESS BAR
# ═══════════════════════════════════════════════════════════════════════════════

class ProgressBar(MDBoxLayout):
    """
    Styled progress bar.

    Usage:
        ProgressBar:
            value: 75  # 0-100
            color: app.theme_cls.primary
    """

    value = NumericProperty(0)  # 0-100
    bar_color = ColorProperty(Colors.PRIMARY)
    bg_color = ColorProperty(Colors.BG_INPUT)
    height = NumericProperty(dp(6))
    radius = NumericProperty(dp(3))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = self.height
        self.bind(
            pos=self._draw,
            size=self._draw,
            value=self._draw,
        )
        Clock.schedule_once(self._draw, 0)

    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Background
            Color(*self.bg_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.radius],
            )
            # Fill
            fill_width = max(0, (self.value / 100.0) * self.width)
            if fill_width > 0:
                Color(*self.bar_color)
                RoundedRectangle(
                    pos=self.pos,
                    size=(fill_width, self.height),
                    radius=[self.radius],
                )


# ═══════════════════════════════════════════════════════════════════════════════
#  DIVIDER
# ═══════════════════════════════════════════════════════════════════════════════

class Divider(MDBoxLayout):
    """Styled divider/separator line."""

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
            Rectangle(pos=self.pos, size=self.size)
