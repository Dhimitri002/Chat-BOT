# ═══════════════════════════════════════════════════════════════
# Flora Platform — Navigation Drawer Component
# ═══════════════════════════════════════════════════════════════
# Menu lateral de navegação com itens e informações do usuário.
# ═══════════════════════════════════════════════════════════════

from kivy.metrics import dp
from kivy.properties import (
    ListProperty,
    StringProperty,
    ObjectProperty,
    BooleanProperty,
)
from kivy.clock import Clock

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.divider import MDDivider
from kivymd.uix.card import MDCard


# ── Menu Items Definition ────────────────────────────────────────────
MENU_ITEMS = [
    {"icon": "view-dashboard", "label": "Painel", "screen": "dashboard"},
    {"icon": "robot", "label": "Bots", "screen": "bots"},
    {"icon": "key-variant", "label": "Licenças", "screen": "licenses"},
    {"icon": "account-group", "label": "Usuários", "screen": "users"},
    {"icon": "tag-multiple", "label": "Planos", "screen": "plans"},
    {"icon": "chart-line", "label": "Analytics", "screen": "analytics"},
    {"icon": "whatsapp", "label": "WhatsApp", "screen": "whatsapp"},
    {"icon": "cog", "label": "Configurações", "screen": "settings"},
]


class NavDrawerContent(MDBoxLayout):
    """Conteúdo do menu lateral de navegação."""

    selected_screen = StringProperty("dashboard")
    """Nome da tela atualmente selecionada."""

    user_name = StringProperty("Admin")
    """Nome do usuário logado."""

    user_email = StringProperty("admin@flora.bot")
    """Email do usuário logado."""

    on_menu_select = ObjectProperty(None)
    """Callback quando um item do menu é selecionado."""

    on_logout = ObjectProperty(None)
    """Callback para logout."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [dp(0), dp(16)]
        self.spacing = dp(4)
        self.md_bg_color = (0.094, 0.114, 0.243, 1)  # BG_INPUT
        self._build()

    def _build(self):
        """Constrói o menu lateral."""
        # ── Header com info do usuário ──────────────────────────
        header = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(140),
            padding=[dp(20), dp(16)],
            spacing=dp(4),
        )

        # Logo / Título
        title = MDLabel(
            text="Flora Platform",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),  # PRIMARY
            font_style="H5",
            bold=True,
            size_hint_y=None,
            height=dp(36),
        )

        # Subtítulo
        subtitle = MDLabel(
            text="Painel Admin",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),  # TEXT_SECONDARY
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        )

        # Info do usuário
        user_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(0),
        )

        user_name_lbl = MDLabel(
            text=self.user_name,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="Body2",
            bold=True,
            size_hint_y=None,
            height=dp(20),
        )
        self.bind(user_name=lambda inst, val: setattr(user_name_lbl, "text", val))

        user_email_lbl = MDLabel(
            text=self.user_email,
            theme_text_color="Custom",
            text_color=(0.376, 0.49, 0.545, 1),  # TEXT_MUTED
            font_style="Caption",
            size_hint_y=None,
            height=dp(18),
        )
        self.bind(user_email=lambda inst, val: setattr(user_email_lbl, "text", val))

        user_box.add_widget(user_name_lbl)
        user_box.add_widget(user_email_lbl)

        header.add_widget(title)
        header.add_widget(subtitle)
        header.add_widget(user_box)

        self.add_widget(header)

        # ── Divider ─────────────────────────────────────────────
        self.add_widget(MDDivider())

        # ── Menu Items ──────────────────────────────────────────
        self._menu_buttons = {}
        for item in MENU_ITEMS:
            is_selected = item["screen"] == self.selected_screen
            btn = MDFlatButton(
                text=item["label"],
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1) if is_selected else (0.69, 0.745, 0.773, 1),
                font_style="Button",
                size_hint_y=None,
                height=dp(48),
                pos_hint={"x": 0},
                md_bg_color=(0.424, 0.388, 1.0, 0.15) if is_selected else (0, 0, 0, 0),
            )
            btn.bind(on_release=lambda b, s=item["screen"]: self._on_item_click(s))
            self._menu_buttons[item["screen"]] = btn
            self.add_widget(btn)

        # ── Spacer ──────────────────────────────────────────────
        spacer = MDBoxLayout(size_hint_y=1)
        self.add_widget(spacer)

        # ── Divider ─────────────────────────────────────────────
        self.add_widget(MDDivider())

        # ── Logout Button ───────────────────────────────────────
        logout_btn = MDFlatButton(
            text="Sair",
            theme_text_color="Custom",
            text_color=(0.957, 0.263, 0.212, 1),  # ERROR
            font_style="Button",
            size_hint_y=None,
            height=dp(48),
            pos_hint={"x": 0},
        )
        logout_btn.bind(on_release=lambda b: self._on_logout_click())
        self.add_widget(logout_btn)

    def _on_item_click(self, screen_name: str):
        """Handler para clique em item do menu."""
        self.selected_screen = screen_name
        self._update_selection()
        if self.on_menu_select:
            self.on_menu_select(screen_name)

    def _on_logout_click(self):
        """Handler para clique em sair."""
        if self.on_logout:
            self.on_logout()

    def _update_selection(self):
        """Atualiza o estado visual dos itens do menu."""
        for screen_name, btn in self._menu_buttons.items():
            is_selected = screen_name == self.selected_screen
            btn.text_color = (1, 1, 1, 1) if is_selected else (0.69, 0.745, 0.773, 1)
            btn.md_bg_color = (0.424, 0.388, 1.0, 0.15) if is_selected else (0, 0, 0, 0)

    def set_screen(self, screen_name: str):
        """Define a tela selecionada programaticamente."""
        self.selected_screen = screen_name
        self._update_selection()
