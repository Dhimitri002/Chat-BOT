"""
LicensesScreen — Admin license management.

Fetches from GET /api/v1/admin/licenses which returns:
  { "licenses": [ { "id", "license_key", "user_id", "plan_id", "status", "expires_at", "created_at" } ], "total", ... }

Key field mapping:
  - License.license_key  (not key)
  - License.user_id      (not owner_id)
  - License.plan_id
  - License.status       (active, expired, revoked, pending)
"""

from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog

from app_admin.styles.theme import Colors, Theme
from app_admin.utils.constants import status_color, display_status


class LicensesScreen(MDScreen):
    """List, create, and revoke licenses."""

    def __init__(self, app: "FloraAdminApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._licenses: list = []
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

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=Theme.SPACE_SM,
        )
        header.add_widget(MDLabel(
            text="Licenças",
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=0.5,
        ))
        header.add_widget(MDRaisedButton(
            text="Nova Licença",
            size_hint_x=None,
            width=dp(130),
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.BG_BASE,
            on_release=self._open_create_dialog,
        ))
        header.add_widget(MDRaisedButton(
            text="Atualizar",
            size_hint_x=None,
            width=dp(120),
            md_bg_color=Colors.BG_INPUT,
            text_color=Colors.TEXT_SECONDARY,
            on_release=lambda *a: self.load_data(),
        ))
        root.add_widget(header)

        # License list
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
        if not self._licenses:
            self.load_data()

    # ── data loading ─────────────────────────────────────────────────────
    def load_data(self):
        self._clear_list()
        spinner = MDSpinner(size_hint=(None, None), size=(dp(48), dp(48)))
        spinner.active = True
        self._list_container.add_widget(spinner)

        def _fetch():
            try:
                resp = self._app.api.admin_list_licenses(page=self._page)
                licenses = resp.get("licenses", [])
                self._total = resp.get("total", 0)
                Clock.schedule_once(lambda dt: self._render(licenses), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, e=e: self._show_error(str(e)), 0)

        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _render(self, licenses: list):
        self._licenses = licenses
        self._clear_list()

        if not licenses:
            self._list_container.add_widget(MDLabel(
                text="Nenhuma licença encontrada.",
                font_style="Body1",
                halign="center",
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                size_hint_y=None,
                height=dp(48),
            ))
            return

        for lic in licenses:
            card = self._build_license_card(lic)
            self._list_container.add_widget(card)

        self._list_container.add_widget(MDLabel(
            text=f"Total: {self._total} licenças",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_y=None,
            height=dp(30),
        ))

    def _build_license_card(self, lic: dict) -> MDCard:
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

        # Icon
        status = lic.get("status", "unknown")
        icon_color = status_color(status)
        icon_btn = MDIconButton(
            icon="certificate",
            theme_text_color="Custom",
            text_color=icon_color,
            size_hint_x=None,
            width=dp(44),
        )
        card.add_widget(icon_btn)

        # Info
        info = MDBoxLayout(orientation="vertical", spacing=dp(2))
        license_key = lic.get("license_key", "N/A")
        # Show truncated key
        display_key = license_key[:12] + "..." if len(license_key) > 12 else license_key
        info.add_widget(MDLabel(
            text=display_key,
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            shorten=True,
        ))
        user_id = lic.get("user_id", "N/A")
        plan_id = lic.get("plan_id", "N/A")
        expires = lic.get("expires_at", "")
        if expires and "T" in expires:
            expires = expires.split("T")[0]
        info.add_widget(MDLabel(
            text=f"User: {user_id}  |  Plan: {plan_id}  |  Expira: {expires}",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            shorten=True,
        ))
        card.add_widget(info)

        # Status badge
        status_lbl = MDLabel(
            text=display_status(status),
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=icon_color,
            size_hint_x=None,
            width=dp(80),
        )
        card.add_widget(status_lbl)

        # Actions
        actions = MDBoxLayout(
            orientation="horizontal",
            size_hint_x=None,
            width=dp(48),
            spacing=dp(4),
        )
        if status == "active":
            actions.add_widget(MDIconButton(
                icon="close-circle",
                theme_text_color="Custom",
                text_color=Colors.HIGHLIGHT,
                on_release=lambda *a, l=lic: self._revoke_license(l),
            ))
        card.add_widget(actions)

        return card

    # ── create license dialog ────────────────────────────────────────────
    def _open_create_dialog(self, *args):
        content = MDBoxLayout(
            orientation="vertical",
            spacing=Theme.SPACE_SM,
            padding=Theme.SPACE_MD,
            size_hint_y=None,
            height=dp(120),
        )
        self._new_user_id_field = MDTextField(
            hint_text="User ID",
            mode="round",
            icon_left="account",
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            radius=[Theme.RADIUS_MEDIUM],
        )
        content.add_widget(self._new_user_id_field)

        self._new_plan_id_field = MDTextField(
            hint_text="Plan ID",
            mode="round",
            icon_left="credit-card",
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            radius=[Theme.RADIUS_MEDIUM],
        )
        content.add_widget(self._new_plan_id_field)

        self._dialog = MDDialog(
            title="Nova Licença",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="Cancelar",
                    theme_text_color="Custom",
                    text_color=Colors.TEXT_SECONDARY,
                    on_release=lambda *a: self._dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="Criar",
                    md_bg_color=Colors.PRIMARY,
                    text_color=Colors.BG_BASE,
                    on_release=self._do_create_license,
                ),
            ],
        )
        self._dialog.open()

    def _do_create_license(self, *args):
        user_id = (self._new_user_id_field.text or "").strip()
        plan_id = (self._new_plan_id_field.text or "").strip()

        if not user_id or not plan_id:
            self._app.show_snackbar("Preencha User ID e Plan ID.", (*Colors.HIGHLIGHT[:3], 1))
            return

        self._dialog.dismiss()

        def _do():
            try:
                self._app.api.admin_create_license({"user_id": user_id, "plan_id": plan_id})
                Clock.schedule_once(lambda dt: self.load_data(), 0)
                self._app.show_snackbar("Licença criada com sucesso!")
            except Exception as e:
                self._app.show_snackbar(f"Erro: {e}", (*Colors.HIGHLIGHT[:3], 1))

        import threading
        threading.Thread(target=_do, daemon=True).start()

    # ── revoke license ───────────────────────────────────────────────────
    def _revoke_license(self, lic: dict):
        license_id = lic.get("id", "")
        if not license_id:
            return

        def _do():
            try:
                self._app.api.admin_revoke_license(license_id)
                Clock.schedule_once(lambda dt: self.load_data(), 0)
                self._app.show_snackbar("Licença revogada.")
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
