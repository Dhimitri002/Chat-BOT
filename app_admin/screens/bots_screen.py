"""
Bots Screen for the Flora Admin Panel.
Bot management with status indicators, search, and controls.
"""
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.chip import MDChip

from app_admin.services.api_client import api_client
from app_admin.utils.constants import Colors, BOT_STATUS_LABELS
from app_admin.utils.helpers import format_datetime, get_status_color


class BotListItem(MDCard):
    """A single bot list item."""

    def __init__(self, bot_data=None, **kwargs):
        super().__init__(
            orientation="horizontal",
            padding=dp(12),
            spacing=dp(12),
            md_bg_color=Colors.BG_SURFACE,
            radius=[dp(8)],
            elevation=dp(2),
            size_hint_y=None,
            height=dp(80),
            **kwargs,
        )
        self.bot_data = bot_data or {}
        self._build()

    def _build(self):
        data = self.bot_data
        status = data.get("status", "disconnected")
        status_color = get_status_color(status, BOT_STATUS_LABELS)

        # Status indicator
        status_indicator = MDIconButton(
            icon="circle",
            icon_size=dp(12),
            theme_icon_color="Custom",
            icon_color=status_color,
            size_hint_x=None,
            width=dp(32),
            disabled=True,
        )
        self.add_widget(status_indicator)

        # Bot icon
        bot_icon = MDIconButton(
            icon="robot",
            icon_size=dp(28),
            theme_icon_color="Custom",
            icon_color=Colors.PRIMARY_LIGHT,
            size_hint_x=None,
            width=dp(40),
            disabled=True,
        )
        self.add_widget(bot_icon)

        # Info
        info = MDBoxLayout(orientation="vertical", spacing=dp(2))

        name = data.get("name", "Sem nome")
        user_name = data.get("user_name", "Desconhecido")
        name_label = MDLabel(
            text=f"[b]{name}[/b]  -  {user_name}",
            markup=True,
            font_style="Body1",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            shorten=True,
            shorten_from="right",
        )
        info.add_widget(name_label)

        # Status chip and details
        sub_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(24),
        )

        status_text = BOT_STATUS_LABELS.get(status, status)
        status_chip = MDChip(
            text=status_text,
            md_bg_color=(*status_color[:3], 0.2),
            text_color=status_color,
            icon="",
        )
        sub_row.add_widget(status_chip)

        # WhatsApp status
        wa_connected = data.get("whatsapp_connected", False)
        wa_icon = "whatsapp" if wa_connected =="help-circle-outline"
        wa_color = Colors.SUCCESS if wa_connected else Colors.TEXT_HINT
        wa_label = MDLabel(
            text=f"[font=Icons]{'✓' if wa_connected else '✗'}[/font] WhatsApp",
            markup=True,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=wa_color,
        )
        sub_row.add_widget(wa_label)

        # Messages count
        msg_count = data.get("messages_today", 0)
        msg_label = MDLabel(
            text=f"{msg_count} msgs hoje",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
        )
        sub_row.add_widget(msg_label)

        info.add_widget(sub_row)
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

        if status == "paused":
            action_icon = "play"
            action_color = Colors.SUCCESS
        else:
            action_icon = "pause"
            action_color = Colors.WARNING

        toggle_btn = MDIconButton(
            icon=action_icon,
            theme_icon_color="Custom",
            icon_color=action_color,
            on_release=lambda x: self._on_toggle(),
        )
        actions.add_widget(toggle_btn)

        self.add_widget(actions)

    def _on_view(self):
        if self.parent and hasattr(self.parent, "parent") and hasattr(self.parent.parent, "show_bot_details"):
            self.parent.parent.show_bot_details(self.bot_data)

    def _on_toggle(self):
        if self.parent and hasattr(self.parent, "parent") and hasattr(self.parent.parent, "toggle_bot"):
            self.parent.parent.toggle_bot(self.bot_data)


class BotsScreen(MDScreen):
    """Bot management screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "bots"
        self._bots = []
        self._page = 1
        self._build_ui()

    def _build_ui(self):
        """Build the bots screen UI."""
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
            text="Gerenciar Bots",
            font_style="H6",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            bold=True,
        )
        header.add_widget(header_title)

        header.add_widget(MDBoxLayout())

        refresh_btn = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color=Colors.TEXT_SECONDARY,
            on_release=self._load_bots,
        )
        header.add_widget(refresh_btn)

        main_layout.add_widget(header)

        # Filter bar
        filter_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(16), dp(4)],
            spacing=dp(8),
            md_bg_color=Colors.BG_DARK,
        )

        self.search_field = MDTextField(
            hint_text="Buscar bots...",
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
            size_hint_x=0.6,
            on_text_validate=self._on_search,
        )
        filter_bar.add_widget(self.search_field)

        # Status filter chips
        self.status_all = MDChip(
            text="Todos",
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.TEXT_PRIMARY,
            icon="",
            on_release=lambda x: self._filter_status(""),
        )
        filter_bar.add_widget(self.status_all)

        self.status_connected = MDChip(
            text="Online",
            md_bg_color=Colors.BG_SURFACE,
            text_color=Colors.TEXT_SECONDARY,
            icon="",
            on_release=lambda x: self._filter_status("connected"),
        )
        filter_bar.add_widget(self.status_connected)

        self.status_paused = MDChip(
            text="Pausados",
            md_bg_color=Colors.BG_SURFACE,
            text_color=Colors.TEXT_SECONDARY,
            icon="",
            on_release=lambda x: self._filter_status("paused"),
        )
        filter_bar.add_widget(self.status_paused)

        main_layout.add_widget(filter_bar)

        # Bots list
        self.bots_list = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(8)],
            spacing=dp(8),
            size_hint_y=None,
        )
        self.bots_list.bind(minimum_height=self.bots_list.setter("height"))

        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(4))
        scroll.add_widget(self.bots_list)
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
        self._current_status_filter = ""

    def _open_drawer(self, *args):
        nav_drawer = self.manager.parent.ids.get("nav_drawer") if hasattr(self.manager.parent, "ids") else None
        if nav_drawer:
            nav_drawer.set_state("open")

    def on_pre_enter(self):
        self._load_bots()

    def _load_bots(self, *args):
        """Load bots from API."""
        self.loading_box.height = dp(60)
        self.loading_spinner.active = True
        self.bots_list.clear_widgets()

        def _on_data(result, error):
            self.loading_box.height = dp(0)
            self.loading_spinner.active = False

            if error:
                self._show_placeholder(f"Erro: {error.message}")
                return

            if result:
                bots = result.get("bots", result.get("items", []))
                self._bots = bots
                self._update_list()

        search = self.search_field.text.strip()
        api_client.get_bots_async(
            _on_data,
            page=self._page,
            search=search,
            status=self._current_status_filter,
        )

    def _update_list(self):
        """Update the bots list display."""
        self.bots_list.clear_widgets()

        if not self._bots:
            self._show_placeholder("Nenhum bot encontrado")
            return

        for bot in self._bots:
            item = BotListItem(bot_data=bot)
            self.bots_list.add_widget(item)

        self.page_label.text = f"Pagina {self._page}"

    def _show_placeholder(self, text):
        label = MDLabel(
            text=text,
            halign="center",
            font_style="Body1",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_y=None,
            height=dp(60),
        )
        self.bots_list.add_widget(label)

    def _on_search(self, *args):
        self._page = 1
        self._load_bots()

    def _filter_status(self, status):
        self._current_status_filter = status
        self._page = 1
        self._load_bots()

    def _prev_page(self, *args):
        if self._page > 1:
            self._page -= 1
            self._load_bots()

    def _next_page(self, *args):
        self._page += 1
        self._load_bots()

    def show_bot_details(self, bot_data):
        """Show bot details in a dialog."""
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(350),
            padding=dp(8),
        )

        status = bot_data.get("status", "disconnected")
        status_color = get_status_color(status, BOT_STATUS_LABELS)

        fields = [
            ("Nome", bot_data.get("name", "N/A")),
            ("Status", BOT_STATUS_LABELS.get(status, status)),
            ("Dono", bot_data.get("user_name", "N/A")),
            ("Modelo LLM", bot_data.get("llm_model", "N/A")),
            ("Provedor LLM", bot_data.get("llm_provider", "N/A")),
            ("Mensagens hoje", str(bot_data.get("messages_today", 0))),
            ("Total de mensagens", str(bot_data.get("total_messages", 0))),
            ("Prefixo de comando", bot_data.get("command_prefix", "/")),
            ("Criado em", format_datetime(bot_data.get("created_at"))),
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
                size_hint_x=0.4,
            ))
            row.add_widget(MDLabel(
                text=str(value),
                font_style="Body2",
                theme_text_color="Custom",
                text_color=Colors.TEXT_PRIMARY,
                size_hint_x=0.6,
                shorten=True,
            ))
            content.add_widget(row)

        self.dialog = MDDialog(
            title="Detalhes do Bot",
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

    def toggle_bot(self, bot_data):
        """Pause or resume a bot."""
        bot_id = bot_data.get("id", "")
        status = bot_data.get("status", "")

        if status == "paused":
            api_client.resume_bot(bot_id)
        else:
            api_client.pause_bot(bot_id)

        Clock.schedule_once(lambda dt: self._load_bots(), 0.5)
