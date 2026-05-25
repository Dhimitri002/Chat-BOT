"""Loading Overlay - Overlay de carregamento."""
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.utils import get_color_from_hex
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar


class LoadingOverlay(MDBoxLayout):
    """Overlay de carregamento com animacao."""

    message = StringProperty("Carregando...")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, 1)
        self.padding = dp(40)
        self.spacing = dp(20)

        with self.canvas.before:
            Color(0, 0, 0, 0.75)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Spinner (progress bar indeterminado simulada)
        self._spinner = MDProgressBar(
            type="indeterminate",
            size_hint_x=0.6,
            pos_hint={"center_x": 0.5},
            running_duration=0.5,
            catching_duration=0.5,
        )

        # Label
        self._label = MDLabel(
            text=self.message,
            halign="center",
            font_style="Body1",
            theme_text_color="Custom",
            text_color=get_color_from_hex("#ffffff"),
        )

        self.add_widget(self._spinner)
        self.add_widget(self._label)

    def on_message(self, instance, value):
        if hasattr(self, "_label"):
            self._label.text = value

    def _update_bg(self, *args):
        if hasattr(self, "_bg"):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def start(self):
        """Inicia a animacao de loading."""
        self.opacity = 0
        anim_tog = Animation(opacity=1, duration=0.3)
        anim_tog.start(self)
        if hasattr(self, "_spinner"):
            self._spinner.start()

    def stop(self):
        """Para e esconde o overlay."""
        anim_tog = Animation(opacity=0, duration=0.3)
        anim_tog.bind(on_complete=lambda *a: self._cleanup())
        anim_tog.start(self)

    def _cleanup(self):
        if hasattr(self, "_spinner"):
            self._spinner.stop()
