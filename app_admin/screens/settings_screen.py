"""
SettingsScreen — Admin configuration panel.

Sections:
  - API / server settings
  - LLM provider configuration
  - Notification preferences
  - System info & version
"""

from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.switch import MDSwitch
from kivymd.uix.divider import MDDivider
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog

from app_admin.styles.theme import Colors, Theme


class SettingsScreen(MDScreen):
    """Application and platform configuration."""

    def __init__(self, app: "FloraAdminApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
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
            text="Configurações",
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        ))
        header.add_widget(MDBoxLayout())  # spacer
        header.add_widget(MDRaisedButton(
            text="Salvar Tudo",
            size_hint_x=None,
            width=dp(130),
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.BG_BASE,
            on_release=self._save_all,
        ))
        root.add_widget(header)

        # Content
        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(2))
        self._content = MDBoxLayout(
            orientation="vertical",
            spacing=Theme.SPACE_LG,
            padding=[0, 0, 0, Theme.SPACE_LG],
            size_hint_y=None,
        )
        self._content.bind(minimum_height=self._content.setter("height"))
        scroll.add_widget(self._content)
        root.add_widget(scroll)

        self.add_widget(root)
        self._load_current_settings()

    def on_enter(self, *args):
        self._load_current_settings()

    # ── load settings ────────────────────────────────────────────────────
    def _load_current_settings(self):
        self._content.clear_widgets()

        # ── Section: API / Server ────────────────────────────────────
        self._content.add_widget(MDLabel(
            text="API & Servidor",
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.PRIMARY,
            size_hint_y=None,
            height=dp(32),
        ))

        api_card = MDCard(
            orientation="vertical",
            padding=Theme.SPACE_LG,
            spacing=Theme.SPACE_MD,
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_LARGE],
            elevation=Theme.ELEVATION_LOW,
            size_hint_y=None,
        )
        api_card.bind(minimum_height=api_card.setter("height"))

        self._api_url_field = MDTextField(
            hint_text="API Base URL",
            mode="round",
            text="http://localhost:8000/api/v1",
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            radius=[Theme.RADIUS_MEDIUM],
        )
        api_card.add_widget(self._api_url_field)

        self._api_key_field = MDTextField(
            hint_text="Chave de API (Global)",
            mode="round",
            password=True,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            radius=[Theme.RADIUS_MEDIUM],
        )
        api_card.add_widget(self._api_key_field)

        self._content.add_widget(api_card)

        # ── Section: LLM Provider ────────────────────────────────────
        self._content.add_widget(MDLabel(
            text="Provedor LLM",
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.PRIMARY,
            size_hint_y=None,
            height=dp(32),
        ))

        llm_card = MDCard(
            orientation="vertical",
            padding=Theme.SPACE_LG,
            spacing=Theme.SPACE_MD,
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_LARGE],
            elevation=Theme.ELEVATION_LOW,
            size_hint_y=None,
        )
        llm_card.bind(minimum_height=llm_card.setter("height"))

        self._llm_key_field = MDTextField(
            hint_text="OpenAI / Gemini API Key",
            mode="round",
            password=True,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            fill_color_focus=Colors.BG_INPUT,
            radius=[Theme.RADIUS_MEDIUM],
        )
        llm_card.add_widget(self._llm_key_field)

        # Model switch row
        model_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            padding=[Theme.SPACE_SM, 0],
        )
        model_row.add_widget(MDLabel(
            text="Modo Avançado (GPT-4)",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
        ))
        model_row.add_widget(MDBoxLayout())  # spacer
        self._advanced_switch = MDSwitch(
            pos_hint={"center_y": 0.5},
        )
        self._active_widget = self._advanced_switch
        self._active_widget.active = False
        model_row.add_widget(self._active_widget)
        llm_card.add_widget(model_row)

        self._content.add_widget(llm_card)

        # ── Section: Notificações ────────────────────────────────────
        self._content.add_widget(MDLabel(
            text="Notificações",
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.PRIMARY,
            size_hint_y=None,
            height=dp(32),
        ))

        notif_card = MDCard(
            orientation="vertical",
            padding=Theme.SPACE_LG,
            spacing=Theme.SPACE_SM,
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_LARGE],
            elevation=Theme.ELEVATION_LOW,
            size_hint_y=None,
        )
        notif_card.bind(minimum_height=notif_card.setter("height"))

        for label_text, default in [
            ("Alertas por email",      False),
            ("Notificações WhatsApp",   True),
            ("Logs de erro",            True),
        ]:
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(40),
            )
            row.add_widget(MDLabel(
                text=label_text,
                font_style="Body2",
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
            ))
            row.add_widget(MDBoxLayout())  # spacer
            sw = MDSwitch(pos_hint={"center_y": 0.5})
            sw.active = default
            row.add_widget(sw)
            notif_card.add_widget(row)

        self._content.add_widget(notif_card)

        # ── Section: System Info ─────────────────────────────────────
        self._content.add_widget(MDLabel(
            text="Sistema",
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.PRIMARY,
            size_hint_y=None,
            height=dp(32),
        ))

        sys_card = MDCard(
            orientation="vertical",
            padding=Theme.SPACE_LG,
            spacing=dp(4),
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_LARGE],
            elevation=Theme.ELEVATION_LOW,
            size_hint_y=None,
            height=dp(120),
        )
        sys_card.add_widget(MDLabel(
            text="Flora Platform v1.0.0",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
        ))
        sys_card.add_widget(MDLabel(
            text="Admin Panel v1.0.0",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
        ))
        sys_card.add_widget(MDLabel(
            text="Python 3.12 | KivyMD 2.0 | FastAPI 0.115",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
        ))
        self._content.add_widget(sys_card)

    # ── save ─────────────────────────────────────────────────────────────
    def _save_all(self, *args):
        self._app.show_snackbar("Configurações salvas com sucesso!")
