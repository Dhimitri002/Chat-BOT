"""
BotsScreen — Admin bot management with premium dark theme.
"""

from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog

from app_admin.styles.theme import Colors, Theme
from app_admin.utils.constants import status_color, display_status


class BotsScreen(MDScreen):
    """List, view, and manage all platform bots."""

    def __init__(self, app: "FloraAdminApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._bots: list = []
        self._page = 1
        self._total = 0
        self._dialog: MDDialog | None = None
        self._build()

    def _build(self):
        root = MDBoxLayout(
            orientation="vertical",
            padding=Theme.SPACE_LG,
            spacing=Theme.SPACE_MD,
            md_bg_color=Colors.BG_BASE,
        )

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=Theme.SPACE_SM,
        )
        header.add_widget(MDLabel(
            text="Bots",
            font_style=Theme.H4,
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=0.7,
        ))
        header.add_widget(MDRaisedButton(
            text="+ Novo Bot",
            size_hint_x=None,
            width=dp(120),
            size_hint_y=None,
            height=dp(36),
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.TEXT_ON_ACCENT,
            theme_text_color="Custom",
            on_release=lambda x: self._app.show_snackbar("Criar novo bot", "info"),
        ))
        root.add_widget(header)

        # Search
        search_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=Theme.SPACE_SM,
        )
        self._search = MDTextField(
            hint_text="Buscar bots...",
            mode="round",
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            icon_right="magnify",
            icon_right_color=Colors.TEXT_HINT,
            radius=dp(12),
        )
        search_row.add_widget(self._search)
        root.add_widget(search_row)

        # Table header
        table_header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            padding=[Theme.SPACE_MD, 0],
            md_bg_color=Colors.BG_SECONDARY,
        )
        for col, w in [("Nome", 0.25), ("Dono", 0.20), ("Status", 0.15), ("Ativo", 0.10), ("Criado", 0.15), ("Ações", 0.15)]:
            table_header.add_widget(MDLabel(
                text=col,
                font_style=Theme.BUTTON_STYLE,
                bold=True,
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
                size_hint_x=w,
                shorten=True,
            ))
        root.add_widget(table_header)

        # Bot list
        scroll = MDScrollView()
        self._bot_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(1),
            size_hint_y=None,
        )
        self._bot_list.bind(minimum_height=self._bot_list.setter("height"))
        scroll.add_widget(self._bot_list)
        root.add_widget(scroll)

        self.add_widget(root)
        self._load_mock_data()

    def _load_mock_data(self):
        self._bots = [
            {"id": 1, "name": "Suporte Bot", "owner": "João Silva", "status": "active", "is_active": True, "created_at": "2025-01-15"},
            {"id": 2, "name": "Vendas Pro", "owner": "Maria Santos", "status": "active", "is_active": True, "created_at": "2025-02-20"},
            {"id": 3, "name": "FAQ Helper", "owner": "Pedro Costa", "status": "inactive", "is_active": False, "created_at": "2025-03-10"},
            {"id": 4, "name": "Atendimento", "owner": "Ana Oliveira", "status": "error", "is_active": True, "created_at": "2025-04-05"},
        ]
        self._render_bots()

    def _render_bots(self):
        self._bot_list.clear_widgets()
        for i, bot in enumerate(self._bots):
            bg = Colors.BG_CARD if i % 2 == 0 else Colors.BG_SECONDARY
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(48),
                padding=[Theme.SPACE_MD, 0],
                md_bg_color=bg,
            )
            # Name
            row.add_widget(MDLabel(
                text=bot["name"],
                font_style=Theme.BODY2,
                theme_text_color="Custom",
                text_color=Colors.TEXT_PRIMARY,
                size_hint_x=0.25,
                shorten=True,
            ))
            # Owner
            row.add_widget(MDLabel(
                text=bot["owner"],
                font_style=Theme.BODY2,
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
                size_hint_x=0.20,
                shorten=True,
            ))
            # Status
            st_color = status_color(bot["status"])
            row.add_widget(MDLabel(
                text=display_status(bot["status"]),
                font_style=Theme.CAPTION_STYLE,
                theme_text_color="Custom",
                text_color=st_color,
                size_hint_x=0.15,
            ))
            # Active
            active_icon = "check-circle" if bot["is_active"] else "close-circle"
            active_color = Colors.SUCCESS if bot["is_active"] else Colors.TEXT_HINT
            row.add_widget(MDIconButton(
                icon=active_icon,
                theme_text_color="Custom",
                text_color=active_color,
                user_font_size=dp(18),
                size_hint_x=0.10,
            ))
            # Created
            row.add_widget(MDLabel(
                text=bot["created_at"],
                font_style=Theme.CAPTION_STYLE,
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                size_hint_x=0.15,
            ))
            # Actions
            actions = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(4),
                size_hint_x=0.15,
            )
            actions.add_widget(MDIconButton(
                icon="cog",
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                user_font_size=dp(18),
            ))
            actions.add_widget(MDIconButton(
                icon="delete",
                theme_text_color="Custom",
                text_color=Colors.ERROR,
                user_font_size=dp(18),
            ))
            row.add_widget(actions)
            self._bot_list.add_widget(row)
