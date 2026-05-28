# ═══════════════════════════════════════════════════════════════
# Flora Platform — Stat Card Component
# ═══════════════════════════════════════════════════════════════
# Card reutilizável para exibir estatísticas com ícone,
# valor, label e indicador de tendência.
# ═══════════════════════════════════════════════════════════════

from kivy.metrics import dp
from kivy.properties import (
    StringProperty,
    NumericProperty,
    ListProperty,
    BooleanProperty,
    ObjectProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton


class StatCard(ButtonBehavior, MDCard):
    """Card de estatística com ícone, valor e label."""

    icon = StringProperty("chart-box")
    """Nome do ícone Material Design."""

    value = StringProperty("0")
    """Valor principal exibido."""

    label = StringProperty("Estatística")
    """Texto descritivo abaixo do valor."""

    trend_value = NumericProperty(0)
    """Valor da tendência (positivo = subiu, negativo = desceu)."""

    trend_visible = BooleanProperty(False)
    """Se o indicador de tendência é visível."""

    icon_color = ListProperty([0.424, 0.388, 1.0, 1])
    """Cor do ícone (padrão: Flora primary)."""

    value_color = ListProperty([1, 1, 1, 1])
    """Cor do valor."""

    _press_time = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.radius = [dp(16)]
        self.elevation = 2
        self.size_hint_y = None
        self.height = dp(120)
        self.padding = dp(16)
        self.md_bg_color = (0.11, 0.165, 0.298, 1)  # BG_CARD
        self._build()

    def _build(self):
        """Constrói o layout interno do card."""
        # Layout principal vertical
        main_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            adaptive_height=True,
        )

        # Linha superior: ícone + tendência
        top_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
        )

        # Ícone
        self._icon_btn = MDIconButton(
            icon=self.icon,
            theme_icon_color="Custom",
            icon_color=self.icon_color,
            icon_size=dp(28),
            pos_hint={"center_y": 0.5},
            size_hint=(None, None),
            size=(dp(40), dp(40)),
        )
        self.bind(icon=self._update_icon)
        self.bind(icon_color=self._update_icon_color)

        # Espaçador
        spacer = MDBoxLayout(size_hint_x=1)

        # Indicador de tendência
        self._trend_label = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color=(0.302, 0.765, 0.314, 1) if self.trend_value >= 0 else (0.957, 0.263, 0.212, 1),
            font_style="Caption",
            halign="right",
            size_hint=(None, None),
            size=(dp(60), dp(20)),
            opacity=1 if self.trend_visible else 0,
        )
        self.bind(trend_value=self._update_trend)
        self.bind(trend_visible=self._update_trend)

        top_row.add_widget(self._icon_btn)
        top_row.add_widget(spacer)
        top_row.add_widget(self._trend_label)

        # Valor principal
        self._value_label = MDLabel(
            text=str(self.value),
            theme_text_color="Custom",
            text_color=self.value_color,
            font_style="H4",
            bold=True,
            size_hint_y=None,
            height=dp(36),
        )
        self.bind(value=self._update_value)

        # Label descritivo
        self._label_widget = MDLabel(
            text=self.label,
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),  # TEXT_SECONDARY
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        )
        self.bind(label=self._update_label)

        main_box.add_widget(top_row)
        main_box.add_widget(self._value_label)
        main_box.add_widget(self._label_widget)

        self.add_widget(main_box)

    def _update_icon(self, instance, value):
        if hasattr(self, "_icon_btn"):
            self._icon_btn.icon = value

    def _update_icon_color(self, instance, value):
        if hasattr(self, "_icon_btn"):
            self._icon_btn.icon_color = value

    def _update_value(self, instance, value):
        if hasattr(self, "_value_label"):
            self._value_label.text = str(value)

    def _update_label(self, instance, value):
        if hasattr(self, "_label_widget"):
            self._label_widget.text = value

    def _update_trend(self, *args):
        if hasattr(self, "_trend_label"):
            if self.trend_visible and self.trend_value != 0:
                sign = "+" if self.trend_value > 0 else ""
                self._trend_label.text = f"{sign}{self.trend_value}%"
                self._trend_label.text_color = (
                    (0.302, 0.765, 0.314, 1) if self.trend_value >= 0
                    else (0.957, 0.263, 0.212, 1)
                )
                self._trend_label.opacity = 1
            else:
                self._trend_label.opacity = 0

    def animate_value(self, target_value, duration=0.5):
        """Anima a transição do valor numérico."""
        try:
            start = float(self.value)
            end = float(target_value)
        except (ValueError, TypeError):
            self.value = str(target_value)
            return

        steps = 20
        interval = duration / steps

        def _step(dt, current_step=0):
            if current_step >= steps:
                self.value = str(target_value)
                return False
            progress = (current_step + 1) / steps
            eased = progress * progress * (3 - 2 * progress)  # smoothstep
            current = start + (end - start) * eased
            if end == int(end):
                self.value = str(int(current))
            else:
                self.value = f"{current:.1f}"
            Clock.schedule_once(_step, interval)
            return False

        Clock.schedule_once(_step, 0)
