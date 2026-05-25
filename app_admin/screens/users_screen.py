"""
UsersScreen — Admin user management.

Fetches from GET /api/v1/admin/users which returns:
  { "users": [ { "id", "email", "name", "role", "is_active", "last_login", "created_at" } ], "total", "page", "page_size" }
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

    # ── build UI ────────────────────────────────────────────────────────
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
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=0.7,
        ))
        header.add_widget(MDRaisedButton(
            text="Atualizar",
            size_hint_x=None,
            width=dp(120),
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.BG_BASE,
            on_release=lambda *a: self.load_data(),
        ))
        root.add_widget(header)

        # Scrollable user list
        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(2))
        self._list_container = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            padding=[0, 0, 0, Theme.SPACE_LG],
            size_hint_y=None,
        )
        self._list_container.bind(minimum_height=self._list_container.setter("height"))
        scroll.add_widget(self._list_container)
        root.add_widget(scroll)

        self.add_widget(root)

    def on_enter(self, *args):
        if not self._users:
            self.load_data()

    # ── data loading ─────────────────────────────────────────────────────
    def load_data(self):
        self._clear_list()
        spinner = MDSpinner(size_hint=(None, None), size=(dp(48), dp(48)))
        spinner.active = True
        self._list_container.add_widget(spinner)

        def _fetch():
            try:
                resp = self._app.api.admin_list_users(page=self._page)
                users = resp.get("users", [])
                self._total = resp.get("total", 0)
                Clock.schedule_once(lambda dt: self._render(users), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, e=e: self._show_error(str(e)), 0)

        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _render(self, users: list):
        self._users = users
        self._clear_list()

        if not users:
            self._list_container.add_widget(MDLabel(
                text="Nenhum usuário encontrado.",
                font_style="Body1",
                halign="center",
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                size_hint_y=None,
                height=dp(48),
            ))
            return

        for user in users:
            card = self._build_user_card(user)
            self._list_container.add_widget(card)

        # Total label
        self._list_container.add_widget(MDLabel(
            text=f"Total: {self._total} usuários",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_y=None,
            height=dp(30),
        ))

    def _build_user_card(self, user: dict) -> MDCard:
        card = MDCard(
            orientation="horizontal",
            padding=Theme.SPACE_MD,
            spacing=Theme.SPACE_MD,
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_MEDIUM],
            elevation=Theme.ELEVATION_LOW,
            size_hint_y=None,
            height=dp(72),
        )

        # Avatar circle
        name = user.get("name", "?")
        initials = "".join(w[0] for w in name.split()[:2]).upper() if name else "?"
        avatar = MDBoxLayout(
            size_hint_x=None,
            width=dp(44),
            md_bg_color=(*Colors.PRIMARY[:3], 0.2),
            radius=[dp(22)],
        )
        avatar.add_widget(MDLabel(
            text=initials,
            font_style="Subtitle1",
            bold=True,
            halign="center",
            valign="center",
            theme_text_color="Custom",
            text_color=Colors.PRIMARY,
        ))
        card.add_widget(avatar)

        # Info
        info = MDBoxLayout(orientation="vertical", spacing=dp(2))
        info.add_widget(MDLabel(
            text=name or "Sem nome",
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            shorten=True,
        ))
        info.add_widget(MDLabel(
            text=user.get("email", ""),
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            shorten=True,
        ))
        card.add_widget(info)

        # Role badge
        role = user.get("role", "user")
        role_label = MDLabel(
            text=display_role(role),
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.PRIMARY if role == "admin" else Colors.TEXT_SECONDARY,
            size_hint_x=None,
            width=dp(100),
        )
        card.add_widget(role_label)

        # Status badge
        is_active = user.get("is_active", True)
        status_text = "Ativo" if is_active else "Inativo"
        status_lbl = MDLabel(
            text=status_text,
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.SUCCESS if is_active else Colors.TEXT_HINT,
            size_hint_x=None,
            width=dp(60),
        )
        card.add_widget(status_lbl)

        # Actions
        actions = MDBoxLayout(
            orientation="horizontal",
            size_hint_x=None,
            width=dp(80),
            spacing=dp(4),
        )
        actions.add_widget(MDIconButton(
            icon="account-edit",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            on_release=lambda *a, u=user: self._edit_user(u),
        ))
        if is_active:
            actions.add_widget(MDIconButton(
                icon="account-cancel",
                theme_text_color="Custom",
                text_color=Colors.HIGHLIGHT,
                on_release=lambda *a, u=user: self._deactivate_user(u),
            ))
        card.add_widget(actions)

        return card

    # ── actions ──────────────────────────────────────────────────────────
    def _edit_user(self, user: dict):
        """Open a simple edit dialog for the user."""
        self._dialog = MDDialog(
            title=f"Editar: {user.get('name', '')}",
            type="custom",
            content_cls=MDBoxLayout(
                orientation="vertical",
                spacing=Theme.SPACE_SM,
                padding=Theme.SPACE_MD,
                size_hint_y=None,
                height=dp(120),
            ),
            buttons=[
                MDFlatButton(
                    text="Cancelar",
                    theme_text_color="Custom",
                    text_color=Colors.TEXT_SECONDARY,
                    on_release=lambda *a: self._dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="Salvar",
                    md_bg_color=Colors.PRIMARY,
                    text_color=Colors.BG_BASE,
                    on_release=lambda *a, u=user: self._save_user(u),
                ),
            ],
        )
        self._dialog.open()

    def _save_user(self, user: dict):
        self._dialog.dismiss()
        self._app.show_snackbar("Usuário atualizado.")

    def _deactivate_user(self, user: dict):
        user_id = user.get("id", "")
        if not user_id:
            return

        def _do():
            try:
                self._app.api.admin_deactivate_user(user_id)
                Clock.schedule_once(lambda dt: self.load_data(), 0)
                self._app.show_snackbar("Usuário desativado.")
            except Exception as e:
                self._app.show_snackbar(f"Erro: {e}", (*Colors.HIGHLIGHT[:3], 1))

        import threading
        threading.Thread(target=_do, daemon=True).start()

    # ── helpers ──────────────────────────────────────────────────────────
    def _clear_list(self):
        self._list_container.clear_widgets()

    def _show_error(self, msg: str):
        self._clear_list()
        self._list_container.add_widget(MDLabel(
            text=f"Erro: {msg}",
            font_style="Body1",
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.HIGHLIGHT,
        ))
