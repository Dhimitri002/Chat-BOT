# ═══════════════════════════════════════════════════════════════
# Flora Platform — Tela de Bots
# ═══════════════════════════════════════════════════════════════

from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.scrollview import ScrollView

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import (
    MDRaisedButton, MDIconButton, MDFlatButton, MDFloatingActionButton
)
from kivymd.uix.card import MDCard
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.textfield import MDTextField
from kivymd.uix.chip import MDChip
from kivymd.uix.dialog import MDDialog
from kivymd.toast import toast

from apps.shared.api_client import api


class BotsScreen(Screen):
    """Tela de gerenciamento de bots."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "bots"
        self._dialog = None
        self._loading = False
        self._bots = []
        self._build()
        Clock.schedule_once(lambda dt: self._load_bots(), 0.5)

    def _build(self):
        """Constrói a tela de bots."""
        self.md_bg_color = (0.059, 0.063, 0.137, 1)

        main_layout = MDBoxLayout(orientation="vertical")

        # ── Toolbar ─────────────────────────────────────────────
        toolbar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(16), dp(8)],
            md_bg_color=(0.11, 0.165, 0.298, 1),
        )

        back_btn = MDIconButton(
            icon="arrow-left",
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            on_release=lambda x: self._go_back(),
        )

        title = MDLabel(
            text="Bots",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6",
            bold=True,
        )

        spacer = MDBoxLayout(size_hint_x=1)

        search_btn = MDIconButton(
            icon="magnify",
            theme_icon_color="Custom",
            icon_color=(0.69, 0.745, 0.773, 1),
            on_release=self._toggle_search,
        )

        refresh_btn = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color=(0.424, 0.388, 1.0, 1),
            on_release=lambda x: self._load_bots(),
        )

        toolbar.add_widget(back_btn)
        toolbar.add_widget(title)
        toolbar.add_widget(spacer)
        toolbar.add_widget(search_btn)
        toolbar.add_widget(refresh_btn)
        main_layout.add_widget(toolbar)

        # ── Barra de Pesquisa ───────────────────────────────────
        self.search_box = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(0),
            opacity=0,
            padding=[dp(16), dp(0)],
        )

        self.search_field = MDTextField(
            hint_text="Buscar bots...",
            mode="round",
            radius=[dp(10)],
            size_hint_x=0.8,
            height=dp(48),
            hint_text_color_normal=(0.376, 0.49, 0.545, 1),
            text_color_normal=(1, 1, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            line_color_normal=(0.227, 0.294, 0.431, 1),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            fill_color_normal=(0.055, 0.106, 0.243, 1),
        )

        search_go = MDIconButton(
            icon="magnify",
            theme_icon_color="Custom",
            icon_color=(0.424, 0.388, 1.0, 1),
            on_release=lambda x: self._load_bots(search=self.search_field.text),
        )

        self.search_box.add_widget(self.search_field)
        self.search_box.add_widget(search_go)
        main_layout.add_widget(self.search_box)

        # ── Filtros ─────────────────────────────────────────────
        filters = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            padding=[dp(16), dp(0)],
            spacing=dp(8),
        )

        filter_all = MDChip(
            text="Todos",
            icon="",
            selected=True,
            md_bg_color=(0.424, 0.388, 1.0, 1),
            text_color=(1, 1, 1, 1),
            on_release=lambda x: self._filter_bots("all"),
        )

        filter_active = MDChip(
            text="Ativos",
            icon="",
            md_bg_color=(0, 0, 0, 0),
            text_color=(0.69, 0.745, 0.773, 1),
            on_release=lambda x: self._filter_bots("active"),
        )

        filter_inactive = MDChip(
            text="Inativos",
            icon="",
            md_bg_color=(0, 0, 0, 0),
            text_color=(0.69, 0.745, 0.773, 1),
            on_release=lambda x: self._filter_bots("inactive"),
        )

        filters.add_widget(filter_all)
        filters.add_widget(filter_active)
        filters.add_widget(filter_inactive)
        filters.add_widget(MDBoxLayout(size_hint_x=1))
        main_layout.add_widget(filters)

        # ── Lista de Bots ───────────────────────────────────────
        scroll = ScrollView()
        self.bots_list = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(8)],
            spacing=dp(12),
            size_hint_y=None,
        )
        self.bots_list.bind(minimum_height=self.bots_list.setter("height"))

        # Loading
        self._loading_box = MDBoxLayout(
            size_hint_y=None,
            height=dp(200),
        )
        self._spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            active=True,
        )
        self._loading_box.add_widget(self._spinner)
        self.bots_list.add_widget(self._loading_box)

        scroll.add_widget(self.bots_list)
        main_layout.add_widget(scroll)

        # ── FAB (Floating Action Button) ────────────────────────
        fab_box = MDBoxLayout(size_hint_y=None, height=dp(80))
        fab = MDFloatingActionButton(
            icon="plus",
            pos_hint={"center_x": 0.92, "center_y": 0.5},
            md_bg_color=(0.424, 0.388, 1.0, 1),
            icon_color=(1, 1, 1, 1),
            on_release=lambda x: self._go_to("bot_form"),
        )
        fab_box.add_widget(fab)
        main_layout.add_widget(fab_box)

        self.add_widget(main_layout)

    def _toggle_search(self, *args):
        """Alterna a visibilidade da barra de pesquisa."""
        if self.search_box.height == 0:
            self.search_box.height = dp(56)
            self.search_box.opacity = 1
            self.search_box.padding = [dp(16), dp(8)]
        else:
            self.search_box.height = dp(0)
            self.search_box.opacity = 0
            self.search_box.padding = [dp(16), dp(0)]

    def _filter_bots(self, filter_type):
        """Filtra a lista de bots."""
        self._current_filter = filter_type
        self._render_bots()

    def _load_bots(self, search=None):
        """Carrega a lista de bots."""
        if self._loading:
            return
        self._loading = True
        self._spinner.active = True
        self._loading_box.height = dp(200)
        self._loading_box.opacity = 1

        params = {}
        if search:
            params["search"] = search

        def _on_result(result):
            Clock.schedule_once(lambda dt: self._handle_bots(result), 0)

        api.get_async("/admin/bots", _on_result, params if params else None)

    def _handle_bots(self, result):
        """Processa os bots recebidos."""
        self._loading = False
        self._loading_box.height = dp(0)
        self._loading_box.opacity = 0
        self._spinner.active = False

        if result.get("error"):
            toast("Erro ao carregar bots.")
            return

        self._bots = result.get("bots", [])
        self._render_bots()

    def _render_bots(self):
        """Renderiza a lista de bots."""
        self.bots_list.clear_widgets()

        bots = self._bots
        filter_type = getattr(self, "_current_filter", "all")

        if filter_type == "active":
            bots = [b for b in bots if b.get("is_active")]
        elif filter_type == "inactive":
            bots = [b for b in bots if not b.get("is_active")]

        if not bots:
            empty = MDBoxLayout(
                size_hint_y=None,
                height=dp(120),
            )
            empty_lbl = MDLabel(
                text="Nenhum bot encontrado.",
                theme_text_color="Custom",
                text_color=(0.376, 0.49, 0.545, 1),
                font_style="Body1",
                halign="center",
            )
            empty.add_widget(empty_lbl)
            self.bots_list.add_widget(empty)
            return

        for bot in bots:
            card = self._create_bot_card(bot)
            self.bots_list.add_widget(card)

    def _create_bot_card(self, bot):
        """Cria um card para um bot."""
        is_active = bot.get("is_active", False)
        is_connected = bot.get("is_connected", False)

        if is_connected:
            status_color = (0.145, 0.827, 0.4, 1)  # WA_CONNECTED
            status_text = "Conectado"
            status_icon="check-circle"
        elif is_active:
            status_color = (0.957, 0.612, 0.0, 1)  # WARNING
            status_text = "Ativo"
            status_icon="alert-circle"
        else:
            status_color = (0.957, 0.263, 0.212, 1)  # ERROR
            status_text = "Inativo"
            status_icon="close-circle"

        card = MDCard(
            orientation="vertical",
            radius=[dp(16)],
            elevation=2,
            padding=dp(16),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(160),
            md_bg_color=(0.11, 0.165, 0.298, 1),
        )

        # Header: nome + status
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
        )

        name_lbl = MDLabel(
            text=bot.get("name", "Sem nome"),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6",
            bold=True,
            size_hint_x=0.7,
        )

        status_chip = MDChip(
            text=f"  {status_text}  ",
            icon=status_icon,
            md_bg_color=(*status_color[:3], 0.15),
            text_color=status_color,
            size_hint_x=None,
            width=dp(110),
            height=dp(28),
            font_size=dp(11),
        )

        header.add_widget(name_lbl)
        header.add_widget(status_chip)
        card.add_widget(header)

        # Info
        info = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(2),
        )

        info.add_widget(MDLabel(
            text=f"ID: {bot.get('id', '')[:8]}...",
            theme_text_color="Custom",
            text_color=(0.376, 0.49, 0.545, 1),
            font_style="Caption",
        ))

        created = bot.get("created_at", "N/A")
        if created and len(str(created)) > 10:
            created = str(created)[:10]
        info.add_widget(MDLabel(
            text=f"Criado: {created}",
            theme_text_color="Custom",
            text_color=(0.376, 0.49, 0.545, 1),
            font_style="Caption",
        ))

        card.add_widget(info)

        # Ações
        actions = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(4),
        )

        edit_btn = MDFlatButton(
            text="Editar",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            font_style="Button",
            on_release=lambda x, b=bot: self._edit_bot(b),
        )

        delete_btn = MDFlatButton(
            text="Excluir",
            theme_text_color="Custom",
            text_color=(0.957, 0.263, 0.212, 1),
            font_style="Button",
            on_release=lambda x, b=bot: self._confirm_delete(b),
        )

        actions.add_widget(edit_btn)
        actions.add_widget(delete_btn)
        actions.add_widget(MDBoxLayout(size_hint_x=1))

        if is_connected:
            disconnect_btn = MDFlatButton(
                text="Desconectar",
                theme_text_color="Custom",
                text_color=(0.957, 0.612, 0.0, 1),
                font_style="Button",
                on_release=lambda x, b=bot: self._disconnect_wa(b),
            )
            actions.add_widget(disconnect_btn)
        else:
            connect_btn = MDFlatButton(
                text="Conectar",
                theme_text_color="Custom",
                text_color=(0.145, 0.827, 0.4, 1),
                font_style="Button",
                on_release=lambda x, b=bot: self._connect_wa(b),
            )
            actions.add_widget(connect_btn)

        card.add_widget(actions)
        return card

    def _edit_bot(self, bot):
        """Abre o formulário de edição."""
        form_screen = self.manager.get_screen("bot_form")
        form_screen.load_bot(bot)
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "bot_form"

    def _confirm_delete(self, bot):
        """Confirma exclusão do bot."""
        if self._dialog:
            self._dialog.dismiss()

        self._dialog = MDDialog(
            title="Excluir Bot",
            text=f'Tem certeza que deseja excluir o bot "{bot.get("name")}"?',
            buttons=[
                MDFlatButton(
                    text="Cancelar",
                    theme_text_color="Custom",
                    text_color=(0.69, 0.745, 0.773, 1),
                    on_release=lambda x: self._dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="Excluir",
                    md_bg_color=(0.957, 0.263, 0.212, 1),
                    text_color=(1, 1, 1, 1),
                    on_release=lambda x: self._delete_bot(bot),
                ),
            ],
        )
        self._dialog.open()

    def _delete_bot(self, bot):
        """Exclui o bot."""
        self._dialog.dismiss()

        def _on_result(result):
            Clock.schedule_once(lambda dt: self._handle_delete(result, bot), 0)

        api.delete_async(f"/admin/bots/{bot.get('id')}", _on_result)

    def _handle_delete(self, result, bot):
        """Processa resultado da exclusão."""
        if result.get("error"):
            toast("Erro ao excluir bot.")
        else:
            toast("Bot excluído com sucesso.")
            self._load_bots()

    def _connect_wa(self, bot):
        """Conecta bot ao WhatsApp."""
        toast("Conectando ao WhatsApp...")
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "whatsapp"

    def _disconnect_wa(self, bot):
        """Desconecta bot do WhatsApp."""
        toast("Desconectando...")

    def _go_back(self):
        """Volta para o dashboard."""
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"

    def _go_to(self, screen):
        """Navega para outra tela."""
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen

    def on_enter(self, *args):
        """Recarrega ao entrar."""
        Clock.schedule_once(lambda dt: self._load_bots(), 0.3)
        return super().on_enter(*args)
