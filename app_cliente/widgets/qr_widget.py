"""QR Widget - Widget de exibicao de QR Code."""
from kivy.graphics import Color, Rectangle, Line
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.utils import get_color_from_hex
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout


class QRWidget(MDCard):
    """Widget que exibe um QR Code (ou placeholder)."""

    qr_data = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.size = (dp(220), dp(220))
        self.pos_hint = {"center_x": 0.5}
        self.radius = [16]
        self.elevation = 4
        self.padding = dp(16)
        self.md_bg_color = get_color_from_hex("#ffffff")
        self.build()

    def build(self):
        # QR Code placeholder - draws a fake QR pattern
        qr_container = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
        )
        self.add_widget(qr_container)

    def on_qr_data(self, instance, value):
        """Atualiza o QR code quando os dados mudam."""
        self.clear_widgets()
        if value:
            self._draw_qr_placeholder(value)
        else:
            self._draw_empty_state()

    def _draw_qr_placeholder(self, data):
        """Desenha um placeholder visual de QR code."""
        from kivy.graphics import Color, Rectangle, Line
        from kivy.metrics import dp

        # Background branco
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)

        # Desenhar padrao QR simulado
        with self.canvas.before:
            Color(0, 0, 0, 1)
            cx, cy = self.center_x, self.center_y
            size = dp(160)
            half = size / 2

            # Quadrado externo
            Line(rectangle=(cx - half, cy - half, size, size), width=1.5)

            # Cantos de posicionamento (3 quadrados grandes)
            corner_size = dp(35)
            offset = dp(10)
            for dx, dy in [(-1, -1), (1, -1), (-1, 1)]:
                x = cx + dx * (half - offset - corner_size / 2)
                y = cy + dy * (half - offset - corner_size / 2)
                Line(rectangle=(x - corner_size / 2, y - corner_size / 2,
                                corner_size, corner_size), width=2)

            # Pontos internos simulados
            import random
            random.seed(hash(data))
            dot_size = dp(6)
            grid_range = range(-5, 6)
            for gx in grid_range:
                for gy in grid_range:
                    if random.random() > 0.5:
                        x = cx + gx * dp(12)
                        y = cy + gy * dp(12)
                        Rectangle(pos=(x - dot_size / 2, y - dot_size / 2),
                                  size=(dot_size, dot_size))

        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _draw_empty_state(self):
        """Estado vazio quando nao ha QR code."""
        label = MDLabel(
            text="Aguardando QR Code...",
            halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex("#757575"),
        )
        self.add_widget(label)

    def _update_canvas(self, *args):
        """Atualiza o canvas quando o widget muda de tamanho/posicao."""
        if hasattr(self, "_bg_rect"):
            self._bg_rect.pos = self.pos
            self._bg_rect.size = self.size
