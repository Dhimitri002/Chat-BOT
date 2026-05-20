"""
Users Screen for the Flora Admin Panel.
User management with search, filter, ban/unban, and details.
"""
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget

from app_admin.services.api_client import api_client
from app_admin.utils.constants import Colors, ROLE_LABELS
from app_admin.utils.helpers import format_datetime, get_status_color


class UserListItem(MDCard):
    """A single user list item."""

    def __init__(self, user_data=None, **kwargs):
        super().__init__(
            orientation="horizontal",
            padding=dp(12),
            spacing=dp(12),
            md_bg_color=Colors.BG_SURFACE,
            radius=[dp(8)],
            elevation=dp(2),
            size_hint_y=None,
            height=dp(72),
            **kwargs,
        )
        self.user_data = user_data or {}
        self._build()

    def _build(self):
        data = self.user_data

        # Avatar
        avatar = MDIconButton(
            icon="account-circle",
            icon_size=dp(32),
            theme_icon_color="Custom",
            icon_color=Colors.PRIMARY_LIGHT,
            size_hint_x=None,
            width=dp(48),
            disabled=True,
        )
        self.add_widget(avatar)

        # Info
        info = MDBoxLayout(orientation="vertical", spacing=dp(2))

        name = data.get("full_name", "Sem nome")
        email = data.get("email", "")
        name_label = MDLabel(
            text=f"[b]{name}[/b]  -  {email}",
            markup=True,
            font_style="Body1",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            shorten=True,
            shorten_from="right",
        )
        info.add_widget(name_label)

        # Role and status
        role = data.get("role", "user")
        is_active = data.get("is_active", True)
        role_text = ROLE_LABELS.get(role, role)
        status_text = "Ativo" if is_active else "Banido"
        status_color = Colors.SUCCESS if is_active else Colors.ERROR

        sub_label = MDLabel(
            text=f"{role_text}  |  [color={self._rgba_to_hex(status_color)}]{status_text}[/color]  |  Criado: {format_datetime(data.get('created_at'))}",
            markup=True,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
        )
        info.add_widget(sub_label)
        self.add_widget(info)

        # Actions
        actions = MDBoxLayout(
            orientation="horizontal",
            size_hint_x=None,
            width=dp(96),
            spacing=dp(4),
        )

        view_btn = MDIconButton(
            icon="eye",
            theme_icon_color="Custom",
            icon_color=Colors.INFO,
            on_release=lambda x: self._on_view(),
        )
        actions.add_widget(view_btn)

        ban_icon = "account-cancel" if is_active else "account-check"
        ban_color = Colors.ERROR if is_active else Colors.SUCCESS
        ban_btn = MDIconButton(
            icon=ban_icon,
            theme_icon_color="Custom",
            icon_color=ban_color,
            on_release=lambda x: self._on_ban(),
        )
        actions.add_widget(ban_btn)

        self.add_widget(actions)

    def _rgba_to_hex(self, rgba):
        """Convert RGBA tuple to hex color string."""
        r = int(rgba[0] * 255)
        g = int(rgba[1] * 255)
        b = int(rgba[2] * 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _on_view(self):
        """View user details."""
        if self.parent and hasattr(self.parent, "parent") and hasattr(self.parent.parent, "show_user_details"):
            self.parent.parent.show_user_details(self.user_data)

    def _on_ban(self):
        """Ban/unban user."""
        if self.parent and hasattr(self.parent, "parent") and hasattr(self.parent.parent, "toggle_ban_user"):
            self.parent.parent.toggle_ban_user(self.user_data)


class UsersScreen(MDScreen):
    """User management screen."""

    search_text = StringProperty("")
    loading = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "users"
        self._users = []
        self._page = 1
        self._build_ui()

    def _build_ui(self):
        """Build the users screen UI."""
        main_layout = MDBoxLayout(
            orientation="vertical",
            md_bg_color=Colors.BG_DARK,
        )

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            padding=[dp(16), dp(8)],
            spacing=dp(8),
            md_bg_color=Colors.BG_CARD,
        )

        menu_btn = MDIconButton(
            icon="menu",
            theme_icon_color="Custom",
            icon_color=Colors.TEXT_PRIMARY,
            on_release=self._open_drawer,
        )
        header.add_widget(menu_btn)

        header_title = MDLabel(
            text="Gerenciar Usuarios",
            font_style="H6",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            bold=True,
        )
        header.add_widget(header_title)

        header.add_widget(MDBoxLayout())  # Spacer

        refresh_btn = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color=Colors.TEXT_SECONDARY,
            on_release=self._load_users,
        )
        header.add_widget(refresh_btn)

        main_layout.add_widget(header)

        # Search and filter bar
        filter_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(16), dp(4)],
            spacing=dp(8),
            md_bg_color=Colors.BG_DARK,
        )

        self.search_field = MDTextField(
            hint_text="Buscar por nome ou email...",
            mode="round",
            icon_left="magnify",
            text="",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            icon_color_normal=Colors.TEXT_SECONDARY,
            icon_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(12)],
            size_hint_x=0.7,
            on_text_validate=self._on_search,
        )
        filter_bar.add_widget(self.search_field)

        filter_btn = MDRaisedButton(
            text="Filtrar",
            md_bg_color=Colors.BG_SURFACE,
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=0.15,
            on_release=self._on_search,
        )
        filter_bar.add_widget(filter_btn)

        clear_btn = MDRaisedButton(
            text="Limpar",
            md_bg_color=Colors.BG_SURFACE,
            text_color=Colors.TEXT_SECONDARY,
            size_hint_x=0.15,
            on_release=self._clear_search,
        )
        filter_bar.add_widget(clear_btn)

        main_layout.add_widget(filter_bar)

        # Users list
        self.users_list = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(8)],
            spacing=dp(8),
            size_hint_y=None,
        )
        self.users_list.bind(minimum_height=self.users_list.setter("height"))

        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(4))
        scroll.add_widget(self.users_list)
        main_layout.add_widget(scroll)

        # Loading
        self.loading_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(0),
            padding=dp(16),
        )
        self.loading_spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            active=False,
            color=Colors.PRIMARY_LIGHT,
            pos_hint={"center_x": 0.5},
        )
        self.loading_box.add_widget(self.loading_spinner)
        main_layout.add_widget(self.loading_box)

        # Pagination
        pagination = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            padding=[dp(16), dp(4)],
            spacing=dp(8),
            md_bg_color=Colors.BG_CARD,
        )

        self.prev_btn = MDRaisedButton(
            text="Anterior",
            md_bg_color=Colors.BG_SURFACE,
            text_color=Colors.TEXT_PRIMARY,
            on_release=self._prev_page,
        )
        pagination.add_widget(self.prev_btn)

        self.page_label = MDLabel(
            text="Pagina 1",
            halign="center",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
        )
        pagination.add_widget(self.page_label)

        self.next_btn = MDRaisedButton(
            text="Proxima",
            md_bg_color=Colors.BG_SURFACE,
            text_color=Colors.TEXT_PRIMARY,
            on_release=self._next_page,
        )
        pagination.add_widget(self.next_btn)

        main_layout.add_widget(pagination)

        self.add_widget(main_layout)

    def _open_drawer(self, *args):
        nav_drawer = self.manager.parent.ids.get("nav_drawer") if hasattr(self.manager.parent, "ids") else None
        if nav_drawer:
            nav_drawer.set_state("open")

    def on_pre_enter(self):
        self._load_users()

    def _load_users(self, *args):
        """Load users from API."""
        self.loading_box.height = dp(60)
        self.loading_spinner.active = True
        self.users_list.clear_widgets()

        def _on_data(result, error):
            self.loading_box.height = dp(0)
            self.loading_spinner.active = False

            if error:
                self._show_placeholder(f"Erro: {error.message}")
                return

            if result:
                users = result.get("users", result.get("items", []))
                self._users = users
                self._update_list()

        search = self.search_field.text.strip()
        api_client.get_users_async(_on_data, page=self._page, search=search)

    def _update_list(self):
        """Update the users list display."""
        self.users_list.clear_widgets()

        if not self._users:
            self._show_placeholder("Nenhum usuario encontrado")
            return

        for user in self._users:
            item = UserListItem(user_data=user)
            self.users_list.add_widget(item)

        self.page_label.text = f"Pagina {self._page}"

    def _show_placeholder(self, text):
        """Show a placeholder message."""
        label = MDLabel(
            text=text,
            halign="center",
            font_style="Body1",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_y=None,
            height=dp(60),
        )
        self.users_list.add_widget(label)

    def _on_search(self, *args):
        """Handle search."""
        self._page = 1
        self._load_users()

    def _clear_search(self, *args):
        """Clear search field."""
        self.search_field.text = ""
        self._page = 1
        self._load_users()

    def _prev_page(self, *args):
        if self._page > 1:
            self._page -= 1
            self._load_users()

    def _next_page(self, *args):
        self._page += 1
        self._load_users()

    def show_user_details(self, user_data):
        """Show user details in a dialog."""
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(300),
            padding=dp(8),
        )

        fields = [
            ("Nome", user_data.get("full_name", "N/A")),
            ("Email", user_data.get("email", "N/A")),
            ("Funcao", ROLE_LABELS.get(user_data.get("role", ""), "N/A")),
            ("Status", "Ativo" if user_data.get("is_active") else "Banido"),
            ("Criado em", format_datetime(user_data.get("created_at"))),
            ("Ultimo login", format_datetime(user_data.get("last_login"))),
        ]

        for label, value in fields:
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(32),
                spacing=dp(8),
            )
            row.add_widget(MDLabel(
                text=f"[b]{label}:[/b]",
                markup=True,
                font_style="Body2",
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
                size_hint_x=0.35,
            ))
            row.add_widget(MDLabel(
                text=str(value),
                font_style="Body2",
                theme_text_color="Custom",
                text_color=Colors.TEXT_PRIMARY,
                size_hint_x=0.65,
                shorten=True,
            ))
            content.add_widget(row)

        self.dialog = MDDialog(
            title="Detalhes do Usuario",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="FECHAR",
                    theme_text_color="Custom",
                    text_color=Colors.PRIMARY_LIGHT,
                    on_release=lambda x: self.dialog.dismiss(),
                ),
            ],
        )
        self.dialog.open()

    def toggle_ban_user(self, user_data):
        """Toggle ban status for a user."""
        user_id = user_data.get("id", "")
        is_active = user_data.get("is_active", True)

        def _on_result(result, error):
            if error:
                return
            self._load_users()

        if is_active:
            api_client.ban_user(user_id)
        else:
            api_client.unban_user(user_id)

        # Reload after a short delay
        Clock.schedule_once(lambda dt: self._load_users(), 0.5)
