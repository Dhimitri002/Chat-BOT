"""
UsersScreen — Admin user management with premium dark theme.
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
from app_admin.utils.constants import display_role, status_color, display_status


class UsersScreen(MDScreen):
    """List, view, and manage platform users."""

    def __init__(self, app: "FloraAdminApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._users: list = []
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

        # Header row
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=Theme.SPACE_SM,
        )
        header.add_widget(MDLabel(
            text="Usuários",
            font_style=Theme.H4,
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=0.7,
        ))
        header.add_widget(MDRaisedButton(
            text="+ Novo",
            size_hint_x=None,
            width=dp(100),
            size_hint_y=None,
            height=dp(36),
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.TEXT_ON_ACCENT,
            theme_text_color="Custom",
            on_release=lambda x: self._app.show_snackbar("Novo usuário", "info"),
        ))
        root.add_widget(header)

        # Search bar
        search_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=Theme.SPACE_SM,
        )
        self._search_field = MDTextField(
            hint_text="Buscar por nome ou email...",
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
        search_row.add_widget(self._search_field)
        root.add_widget(search_row)

        # Table header
        table_header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            padding=[Theme.SPACE_MD, 0],
            md_bg_color=Colors.BG_SECONDARY,
        )
        for col, w in [("Nome", 0.25), ("Email", 0.30), ("Papel", 0.15), ("Status", 0.15), ("Ações", 0.15)]:
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

        # Scrollable user list
        scroll = MDScrollView()
        self._user_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(1),
            size_hint_y=None,
        )
        self._user_list.bind(minimum_height=self._user_list.setter("height"))
        scroll.add_widget(self._user_list)
        root.add_widget(scroll)

        self.add_widget(root)
        self._load_mock_data()

    def _load_mock_data(self):
        """Load mock user data."""
        self._users = [
            {"id": 1, "name": "João Silva", "email": "joao@email.com", "role": "user", "is_active": True},
            {"id": 2, "name": "Maria Santos", "email": "maria@email.com", "role": "admin", "is_active": True},
            {"id": 3, "name": "Pedro Costa", "email": "pedro@email.com", "role": "user", "is_active": False},
            {"id": 4, "name": "Ana Oliveira", "email": "ana@email.com", "role": "user", "is_active": True},
            {"id": 5, "name": "Lucas Ferreira", "email": "lucas@email.com", "role": "user", "is_active": True},
        ]
        self._render_users()

    def _render_users(self):
        self._user_list.clear_widgets()
        for i, user in enumerate(self._users):
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
                text=user["name"],
                font_style=Theme.BODY2,
                theme_text_color="Custom",
                text_color=Colors.TEXT_PRIMARY,
                size_hint_x=0.25,
                shorten=True,
            ))
            # Email
            row.add_widget(MDLabel(
                text=user["email"],
                font_style=Theme.BODY2,
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
                size_hint_x=0.30,
                shorten=True,
            ))
            # Role
            role_color = Colors.SECONDARY if user["role"] == "admin" else Colors.TEXT_SECONDARY
            row.add_widget(MDLabel(
                text=display_role(user["role"]),
                font_style=Theme.CAPTION_STYLE,
                theme_text_color="Custom",
                text_color=role_color,
                size_hint_x=0.15,
            ))
            # Status
            st_color = status_color("active" if user["is_active"] else "inactive")
            row.add_widget(MDLabel(
                text=display_status("active" if user["is_active"] else "inactive"),
                font_style=Theme.CAPTION_STYLE,
                theme_text_color="Custom",
                text_color=st_color,
                size_hint_x=0.15,
            ))
            # Actions
            actions = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(4),
                size_hint_x=0.15,
            )
            actions.add_widget(MDIconButton(
                icon="pencil",
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

            self._user_list.add_widget(row)
