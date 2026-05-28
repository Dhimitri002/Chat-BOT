# ═══════════════════════════════════════════════════════════════
# Flora Platform — Data Table Component
# ═══════════════════════════════════════════════════════════════
# Tabela de dados reutilizável com cabeçalho, linhas e
# suporte a ordenação e seleção.
# ═══════════════════════════════════════════════════════════════

from kivy.metrics import dp
from kivy.properties import (
    ListProperty,
    StringProperty,
    BooleanProperty,
    ObjectProperty,
)
from kivy.clock import Clock

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDFlatButton


class DataTable(MDCard):
    """Tabela de dados com cabeçalho e linhas."""

    columns = ListProperty([])
    """Lista de dicts: [{"key": "name", "label": "Nome", "width": 200}, ...]"""

    data = ListProperty([])
    """Lista de dicts com os dados."""

    sortable = BooleanProperty(True)
    """Se as colunas podem ser ordenadas."""

    empty_message = StringProperty("Nenhum dado encontrado.")
    """Mensagem quando não há dados."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.radius = [dp(16)]
        self.elevation = 2
        self.padding = dp(0)
        self.spacing = dp(0)
        self.md_bg_color = (0.11, 0.165, 0.298, 1)  # BG_CARD
        self.size_hint_y = None
        self.bind(data=self._refresh, columns=self._refresh)
        Clock.schedule_once(lambda dt: self._build(), 0)

    def _build(self):
        """Constrói a tabela."""
        self.clear_widgets()
        if not self.columns:
            return

        # ── Cabeçalho ───────────────────────────────────────────
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            padding=[dp(12), dp(4)],
            md_bg_color=(0.094, 0.114, 0.243, 1),  # BG_INPUT
        )

        for col in self.columns:
            w = col.get("width", 150)
            lbl = MDLabel(
                text=col.get("label", col["key"]),
                theme_text_color="Custom",
                text_color=(0.69, 0.745, 0.773, 1),  # TEXT_SECONDARY
                font_style="Caption",
                bold=True,
                size_hint_x=None,
                width=dp(w),
                halign="left",
                valign="middle",
            )
            lbl.bind(size=lbl.setter("text_size"))
            header.add_widget(lbl)

        self.add_widget(header)

        # ── Separador ───────────────────────────────────────────
        separator = MDBoxLayout(
            size_hint_y=None,
            height=dp(1),
            md_bg_color=(0.227, 0.294, 0.431, 1),  # BG_SURFACE border
        )
        self.add_widget(separator)

        # ── Linhas de Dados ─────────────────────────────────────
        self._rows_container = MDBoxLayout(
            orientation="vertical",
            spacing=dp(1),
            size_hint_y=None,
        )
        self._rows_container.bind(minimum_height=self._rows_container.setter("height"))
        self.add_widget(self._rows_container)

        self._render_rows()

    def _render_rows(self):
        """Renderiza as linhas de dados."""
        self._rows_container.clear_widgets()

        if not self.data:
            empty = MDBoxLayout(
                size_hint_y=None,
                height=dp(80),
            )
            empty_lbl = MDLabel(
                text=self.empty_message,
                theme_text_color="Custom",
                text_color=(0.376, 0.49, 0.545, 1),  # TEXT_MUTED
                font_style="Body1",
                halign="center",
                valign="middle",
            )
            empty.add_widget(empty_lbl)
            self._rows_container.add_widget(empty)
            return

        for i, row in enumerate(self.data):
            row_bg = (0.11, 0.165, 0.298, 1) if i % 2 == 0 else (0.094, 0.114, 0.243, 0.5)

            row_box = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(40),
                padding=[dp(12), dp(4)],
                md_bg_color=row_bg,
            )

            for col in self.columns:
                w = col.get("width", 150)
                key = col["key"]
                cell_value = str(row.get(key, ""))

                cell = MDLabel(
                    text=cell_value,
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    font_style="Body2",
                    size_hint_x=None,
                    width=dp(w),
                    halign="left",
                    valign="middle",
                    shorten=True,
                    shorten_from="right",
                )
                cell.bind(size=cell.setter("text_size"))
                row_box.add_widget(cell)

            self._rows_container.add_widget(row_box)

    def _refresh(self, *args):
        """Atualiza a tabela quando os dados mudam."""
        if hasattr(self, "_rows_container"):
            self._render_rows()
        else:
            self._build()

    def update_data(self, new_data: list):
        """Atualiza os dados da tabela."""
        self.data = new_data
