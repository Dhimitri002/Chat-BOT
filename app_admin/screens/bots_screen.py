"""
BotsScreen — Admin bot management.

Fetches from GET /api/v1/admin/bots which returns:
  { "bots": [ { "id", "name", "owner_id", "status", "is_active", "created_at", ... } ], "total", "page", "page_size" }

Key field mapping:
  - Bot.name       (not bot_name)
  - Bot.owner_id   (not user_id)
  - Bot.status     (string: active, inactive, error, etc.)
  - Bot.is_active  (bool)
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
            text="Bots",
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=0.6,
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

        # Bot list
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
        if not self._bots:
            self.load_data()

    # ── data loading ─────────────────────────────────────────────────────
    def load_data(self):
        self._clear_list()
        spinner = MDSpinner(size_hint=(None, None), size=(dp(48), dp(48)))
        spinner.active = True
        self._list_container.add_widget(spinner)

        def _fetch():
            try:
                resp = self._app.api.admin_list_bots(page=self._page)
                bots = resp.get("bots", [])
                self._total = resp.get("total", 0)
                Clock.schedule_once(lambda dt: self._render(bots), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, e=e: self._show_error(str(e)), 0)

        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _render(self, bots: list):
        self._bots = bots
        self._clear_list()

        if not bots:
            self._list_container.add_widget(MDLabel(
                text="Nenhum bot encontrado.",
                font_style="Body1",
                halign="center",
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                size_hint_y=None,
                height=dp(48),
            ))
            return

        for bot in bots:
            card = self._build_bot_card(bot)
            self._list_container.add_widget(card)

        self._list_container.add_widget(MDLabel(
            text=f"Total: {self._total} bots",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_y=None,
            height=dp(30),
        ))

    def _build_bot_card(self, bot: dict) -> MDCard:
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

        # Bot icon
        is_active = bot.get("is_active", False)
        icon_color = Colors.SUCCESS if is_active else Colors.TEXT_HINT
        icon_btn = MDIconButton(
            icon="robot",
            theme_text_color="Custom",
            text_color=icon_color,
            size_hint_x=None,
            width=dp(44),
        )
        card.add_widget(icon_btn)

        # Info
        info = MDBoxLayout(orientation="vertical", spacing=dp(2))
        info.add_widget(MDLabel(
            text=bot.get("name", "Sem nome"),
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            shorten=True,
        ))
        owner_id = bot.get("owner_id", "N/A")
        created = bot.get("created_at", "")
        if created and "T" in created:
            created = created.split("T")[0]
        info.add_widget(MDLabel(
            text=f"Owner: {owner_id}  |  Criado: {created}",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            shorten=True,
        ))
        card.add_widget(info)

        # Status badge
        status = bot.get("status", "unknown")
        status_lbl = MDLabel(
            text=display_status(status),
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=status_color(status),
            size_hint_x=None,
            width=dp(80),
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
            icon="pencil",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            on_release=lambda *a, b=bot: self._edit_bot(b),
        ))
        if is_active:
            actions.add_widget(MDIconButton(
                icon="stop-circle",
                theme_text_color="Custom",
                text_color=Colors.HIGHLIGHT,
                on_release=lambda *a, b=bot: self._deactivate_bot(b),
            ))
        card.add_widget(actions)

        return card

    # ── actions ──────────────────────────────────────────────────────────
    def _edit_bot(self, bot: dict):
        self._app.show_snackbar(f"Editar bot: {bot.get('name', '')}")

    def _deactivate_bot(self, bot: dict):
        bot_id = bot.get("id", "")
        if not bot_id:
            return

        def _do():
            try:
                self._app.api.admin_deactivate_bot(bot_id)
                Clock.schedule_once(lambda dt: self.load_data(), 0)
                self._app.show_snackbar("Bot desativado.")
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
