"""
BotCreateScreen — Create a new bot owned by a specific user.

Sends POST /api/v1/admin/bots with body:
  { "name": str, "owner_id": str, "welcome_message": str, ... }
"""

from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView

from app_admin.styles.theme import Colors, Theme


class BotCreateScreen(MDScreen):
    """Form to create a new bot on behalf of a user."""

    def __init__(self, app: "FloraAdminApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._build()

    # ── build UI ────────────────────────────────────────────────────────
    def _build(self):
        root = MDBoxLayout(
            orientation="vertical",
            padding=Theme.SPACE_LG,
            spacing=Theme.SPACE_LG,
            md_bg_color=Colors.BG_BASE,
        )

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )
        back_btn = MDIconButton(
            icon="arrow-left",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            on_release=lambda *a: setattr(self.manager, "current", "bots") if self.manager else None,
        )
        header.add_widget(back_btn)
        header.add_widget(MDLabel(
            text="Criar Novo Bot",
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        ))
        root.add_widget(header)

        # Scrollable form area
        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(2))
        form = MDBoxLayout(
            orientation="vertical",
            spacing=Theme.SPACE_LG,
            padding=[Theme.SPACE_LG, Theme.SPACE_LG, Theme.SPACE_LG, Theme.SPACE_2XL],
            size_hint_y=None,
        )
        form.bind(minimum_height=form.setter("height"))
        scroll.add_widget(form)
        root.add_widget(scroll)

        # Form card
        card = MDCard(
            orientation="vertical",
            padding=Theme.SPACE_2XL,
            spacing=Theme.SPACE_LG,
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_XL],
            elevation=Theme.ELEVATION_LOW,
            size_hint_y=None,
        )
        card.bind(minimum_height=card.setter("height"))

        # Icon
        icon_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
        )
        icon_row.add_widget(MDBoxLayout())  # spacer
        icon_row.add_widget(MDIconButton(
            icon="robot",
            theme_text_color="Custom",
            text_color=Colors.PRIMARY,
            user_font_size=dp(40),
            size_hint=(None, None),
            size=(dp(56), dp(56)),
        ))
        icon_row.add_widget(MDBoxLayout())  # spacer
        card.add_widget(icon_row)

        # Name field
        self._name_field = MDTextField(
            hint_text="Nome do Bot",
            mode="round",
            icon_left="robot-outline",
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            radius=[Theme.RADIUS_MEDIUM],
            required=True,
        )
        card.add_widget(self._name_field)

        # Owner ID field
        self._owner_field = MDTextField(
            hint_text="Owner ID (user ID)",
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
            required=True,
        )
        card.add_widget(self._owner_field)

        # Welcome message field
        self._welcome_field = MDTextField(
            hint_text="Mensagem de boas-vindas",
            mode="round",
            icon_left="message-text",
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            radius=[Theme.RADIUS_MEDIUM],
            multiline=False,
        )
        card.add_widget(self._welcome_field)

        # Response style dropdown placeholder (text field for now)
        self._style_field = MDTextField(
            hint_text="Estilo de resposta (ex: formal, casual)",
            mode="round",
            icon_left="palette",
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            radius=[Theme.RADIUS_MEDIUM],
        )
        card.add_widget(self._style_field)

        # Error label
        self._error_label = MDLabel(
            text="",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.HIGHLIGHT,
            size_hint_y=None,
            height=dp(20),
        )
        card.add_widget(self._error_label)

        # Buttons row
        btn_row = MDBoxLayout(
            orientation="horizontal",
            spacing=Theme.SPACE_MD,
            size_hint_y=None,
            height=dp(48),
        )
        btn_row.add_widget(MDBoxLayout())  # spacer
        self._cancel_btn = MDRaisedButton(
            text="Cancelar",
            md_bg_color=Colors.BG_INPUT,
            text_color=Colors.TEXT_SECONDARY,
            radius=[Theme.RADIUS_MEDIUM],
            on_release=self._on_cancel,
        )
        btn_row.add_widget(self._cancel_btn)

        self._create_btn = MDRaisedButton(
            text="Criar Bot",
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.BG_BASE,
            radius=[Theme.RADIUS_MEDIUM],
            on_release=self._on_create,
        )
        btn_row.add_widget(self._create_btn)

        # Spinner (hidden)
        self._spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={"center_x": 0.5},
            active=False,
        )
        btn_row.add_widget(MDBoxLayout())  # spacer
        card.add_widget(btn_row)
        card.add_widget(self._spinner)

        form.add_widget(card)
        self.add_widget(root)

    # ── event handlers ───────────────────────────────────────────────────
    def _on_cancel(self, *args):
        self._clear_fields()
        self._error_label.text = ""
        if self.manager:
            self.manager.current = "bots"

    def _on_create(self, *args):
        name = (self._name_field.text or "").strip()
        owner_id = (self._owner_field.text or "").strip()

        if not name:
            self._error_label.text = "Informe o nome do bot."
            return
        if not owner_id:
            self._error_label.text = "Informe o Owner ID."
            return

        self._error_label.text = ""
        self._create_btn.disabled = True
        self._create_btn.opacity = 0.4
        self._spinner.active = True

        body = {
            "name": name,
            "owner_id": owner_id,
            "welcome_message": (self._welcome_field.text or "").strip(),
            "response_style": (self._style_field.text or "").strip() or "friendly",
        }

        def _do_create():
            try:
                # Using generic request path since the admin bots endpoint is POST /admin/bots
                self._app.api._request("POST", "/admin/bots", body)
                Clock.schedule_once(lambda dt: self._on_success(), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, e=e: self._on_error(str(e)), 0)

        import threading
        threading.Thread(target=_do_create, daemon=True).start()

    def _on_success(self):
        self._spinner.active = False
        self._create_btn.disabled = False
        self._create_btn.opacity = 1
        self._app.show_snackbar("Bot criado com sucesso!")
        self._clear_fields()
        if self.manager:
            self.manager.current = "bots"

    def _on_error(self, msg: str):
        self._spinner.active = False
        self._create_btn.disabled = False
        self._create_btn.opacity = 1
        self._error_label.text = f"Erro: {msg}"

    def _clear_fields(self):
        self._name_field.text = ""
        self._owner_field.text = ""
        self._welcome_field.text = ""
        self._style_field.text = ""
