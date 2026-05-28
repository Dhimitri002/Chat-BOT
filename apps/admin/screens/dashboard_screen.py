# ═══════════════════════════════════════════════════════════════
# Flora Platform — Tela do Painel (Dashboard)
# ═══════════════════════════════════════════════════════════════

from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.anchorlayout import AnchorLayout

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.dialog import MDDialog
from kivymd.toast import toast

from apps.shared.api_client import api
from apps.admin.components.stat_card import StatCard


class DashboardScreen(Screen):
    """Tela principal do painel administrativo."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "dashboard"
        self._dialog = None
        self._loading = False
        self._build()
        Clock.schedule_once(lambda dt: self._load_data(), 0.5)

    def _build(self):
        """Constrói o layout do dashboard."""
        self.md_bg_color = (0.059, 0.063, 0.137, 1)  # BG_DARK

        # Layout principal
        main_layout = MDBoxLayout(orientation="vertical")

        # ── Barra Superior ──────────────────────────────────────
        toolbar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(16), dp(8)],
            md_bg_color=(0.11, 0.165, 0.298, 1),
        )

        menu_btn = MDIconButton(
            icon="menu",
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            on_release=self._open_drawer,
        )

        title = MDLabel(
            text="Painel de Controle",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6",
            bold=True,
        )

        spacer = MDBoxLayout(size_hint_x=1)

        refresh_btn = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color=(0.424, 0.388, 1.0, 1),
            on_release=lambda x: self._load_data(),
        )

        toolbar.add_widget(menu_btn)
        toolbar.add_widget(title)
        toolbar.add_widget(spacer)
        toolbar.add_widget(refresh_btn)
        main_layout.add_widget(toolbar)

        # ── Scroll View com Conteúdo ───────────────────────────
        scroll = ScrollView()
        self.content = MDBoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(16),
            size_hint_y=None,
        )
        self.content.bind(minimum_height=self.content.setter("height"))

        # Loading inicial
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
        self.content.add_widget(self._loading_box)

        scroll.add_widget(self.content)
        main_layout.add_widget(scroll)

        self.add_widget(main_layout)

    def _open_drawer(self, *args):
        """Abre o navigation drawer."""
        nav_drawer = self.manager.parent.parent.nav_drawer
        nav_drawer.set_state("open")

    def _build_dashboard(self, data):
        """Constrói o dashboard com os dados recebidos."""
        self.content.clear_widgets()

        # Saudação
        welcome = MDLabel(
            text="Bem-vindo ao Painel Flora 🌸",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H5",
            bold=True,
            size_hint_y=None,
            height=dp(40),
        )
        self.content.add_widget(welcome)

        subtitle = MDLabel(
            text="Visão geral da plataforma",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Body2",
            size_hint_y=None,
            height=dp(24),
        )
        self.content.add_widget(subtitle)

        # ── Cards de Estatísticas ──────────────────────────────
        stats_data = data if isinstance(data, dict) else {}
        users = stats_data.get("users", {})
        bots = stats_data.get("bots", {})
        licenses = stats_data.get("licenses", {})
        revenue = stats_data.get("revenue", {})
        messages = stats_data.get("messages", {})

        # Primeira linha de cards
        row1 = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(130),
        )

        card_users = StatCard(
            icon="account-group",
            value=str(users.get("total", 0)),
            label="Usuários",
            trend_value=users.get("new_today", 0),
            trend_visible=users.get("new_today", 0) > 0,
            icon_color=(0.129, 0.588, 0.953, 1),  # INFO
        )
        card_users.bind(on_release=lambda x: self._go_to("users"))

        card_bots = StatCard(
            icon="robot",
            value=str(bots.get("total", 0)),
            label="Bots",
            icon_color=(0.424, 0.388, 1.0, 1),  # PRIMARY
        )
        card_bots.bind(on_release=lambda x: self._go_to("bots"))

        card_licenses = StatCard(
            icon="key-variant",
            value=str(licenses.get("active", 0)),
            label="Licenças Ativas",
            icon_color=(0.302, 0.765, 0.314, 1),  # SUCCESS
        )
        card_licenses.bind(on_release=lambda x: self._go_to("licenses"))

        row1.add_widget(card_users)
        row1.add_widget(card_bots)
        row1.add_widget(card_licenses)
        self.content.add_widget(row1)

        # Segunda linha de cards
        row2 = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(130),
        )

        card_messages = StatCard(
            icon="message-text",
            value=str(messages.get("today", 0)),
            label="Mensagens Hoje",
            icon_color=(0.957, 0.612, 0.0, 1),  # WARNING
        )

        card_revenue = StatCard(
            icon="currency-usd",
            value=f"R${revenue.get('total', 0):.0f}",
            label="Receita Total",
            icon_color=(0.424, 0.388, 1.0, 1),
        )

        card_tokens = StatCard(
            icon="brain",
            value=str(stats_data.get("llm", {}).get("tokens_today", 0)),
            label="Tokens Hoje",
            icon_color=(0.914, 0.416, 0.616, 1),  # ACCENT
        )

        row2.add_widget(card_messages)
        row2.add_widget(card_revenue)
        row2.add_widget(card_tokens)
        self.content.add_widget(row2)

        # ── Ações Rápidas ──────────────────────────────────────
        actions_title = MDLabel(
            text="Ações Rápidas",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6",
            bold=True,
            size_hint_y=None,
            height=dp(36),
        )
        self.content.add_widget(actions_title)

        actions_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(56),
        )

        btn_new_bot = MDRaisedButton(
            text="Criar Bot",
            icon="robot",
            md_bg_color=(0.424, 0.388, 1.0, 1),
            text_color=(1, 1, 1, 1),
            radius=[dp(12)],
            size_hint=(None, None),
            size=(dp(140), dp(48)),
            on_release=lambda x: self._go_to("bot_form"),
        )

        btn_new_license = MDRaisedButton(
            text="Nova Licença",
            icon="key-plus",
            md_bg_color=(0.302, 0.765, 0.314, 1),
            text_color=(1, 1, 1, 1),
            radius=[dp(12)],
            size_hint=(None, None),
            size=(dp(160), dp(48)),
            on_release=lambda x: self._go_to("license_form"),
        )

        btn_view_users = MDRaisedButton(
            text="Ver Usuários",
            icon="account-group",
            md_bg_color=(0.129, 0.588, 0.953, 1),
            text_color=(1, 1, 1, 1),
            radius=[dp(12)],
            size_hint=(None, None),
            size=(dp(160), dp(48)),
            on_release=lambda x: self._go_to("users"),
        )

        actions_row.add_widget(btn_new_bot)
        actions_row.add_widget(btn_new_license)
        actions_row.add_widget(btn_view_users)
        actions_row.add_widget(MDBoxLayout(size_hint_x=1))
        self.content.add_widget(actions_row)

        # ── Atividade Recente ──────────────────────────────────
        activity_title = MDLabel(
            text="Status da Plataforma",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6",
            bold=True,
            size_hint_y=None,
            height=dp(36),
        )
        self.content.add_widget(activity_title)

        activity_card = MDCard(
            orientation="vertical",
            radius=[dp(16)],
            elevation=2,
            padding=dp(16),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(140),
            md_bg_color=(0.11, 0.165, 0.298, 1),
        )

        activity_card.add_widget(self._status_row("Usuários Ativos", f"{users.get('active', 0)} / {users.get('total', 0)}", "account-check"))
        activity_card.add_widget(self._status_row("Bots Ativos", f"{bots.get('active', 0)} / {bots.get('total', 0)}", "robot"))
        activity_card.add_widget(self._status_row("Licenças Expirando", str(licenses.get("expiring", 0)), "alert-circle"))
        activity_card.add_widget(self._status_row("Custo LLM Hoje", f"R${stats_data.get('llm', {}).get('cost_today', 0):.4f}", "currency-usd"))

        self.content.add_widget(activity_card)

    def _status_row(self, label, value, icon):
        """Cria uma linha de status."""
        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(28),
        )
        icon_btn = MDIconButton(
            icon=icon,
            theme_icon_color="Custom",
            icon_color=(0.69, 0.745, 0.773, 1),
            icon_size=dp(20),
            size_hint=(None, None),
            size=(dp(32), dp(32)),
        )
        lbl = MDLabel(
            text=label,
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Body2",
            size_hint_x=0.6,
        )
        val = MDLabel(
            text=value,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="Body2",
            bold=True,
            halign="right",
            size_hint_x=0.4,
        )
        row.add_widget(icon_btn)
        row.add_widget(lbl)
        row.add_widget(val)
        return row

    def _load_data(self, *args):
        """Carrega os dados do dashboard."""
        if self._loading:
            return
        self._loading = True

        def _on_result(result):
            Clock.schedule_once(lambda dt: self._handle_data(result), 0)

        api.get_async("/admin/dashboard", _on_result)

    def _handle_data(self, result):
        """Processa os dados recebidos."""
        self._loading = False

        if result.get("error"):
            toast("Erro ao carregar dados. Tente novamente.")
            # Mostra dados vazios
            self._build_dashboard({})
            return

        self._build_dashboard(result)

    def _go_to(self, screen_name):
        """Navega para outra tela."""
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen_name

    def on_enter(self, *args):
        """Quando entra na tela, recarrega dados."""
        Clock.schedule_once(lambda dt: self._load_data(), 0.3)
        return super().on_enter(*args)
