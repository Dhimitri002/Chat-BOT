"""
Flora Admin — Tela de Usuários
================================
Lista todos os usuários com busca, filtros e ações CRUD.
"""

from kivy.clock import Clock
from kivy.metrics import dp

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFloatingActionButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.chip import MDChip
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.textfield import MDTextField
from apps.shared.theme import FloraColors, FloraTheme


class UsersScreen(MDScreen):
    """Tela de gerenciamento de usuários."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self._build_ui()

    def _build_ui(self):
        c = FloraColors()
        layout = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8))

        # Header
        header = MDBoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        title = MDLabel(
            text="👥  Usuários",
            font_style="H4",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
            bold=True,
        )
        header.add_widget(title)
        layout.add_widget(header)

        # Search bar
        search_box = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.search_field = MDTextField(
            hint_text="Buscar por nome ou email...",
            mode="rectangle",
            radius=[FloraTheme.INPUT_RADIUS],
            size_hint_x=0.8,
            line_color_normal=c.to_rgba(c.BG_LIGHT),
            line_color_focus=c.to_rgba(c.PRIMARY_PURPLE),
            hint_text_color_normal=c.to_rgba(c.TEXT_TERTIARY),
            text_color_normal=c.to_rgba(c.TEXT_PRIMARY),
            text_color_focus=c.to_rgba(c.TEXT_PRIMARY),
        )
        self.search_field.bind(on_text_validate=self._on_search)
        search_box.add_widget(self.search_field)

        filter_btn = MDIconIconButton(
            icon="filter-variant",
            theme_icon_color="Custom",
            icon_color=c.to_rgba(c.ACCENT_PINK),
            on_release=self._show_filter,
        )
        search_box.add_widget(filter_btn)
        layout.add_widget(search_box)

        # Stats bar
        stats = MDBoxLayout(size_hint_y=None, height=dp(36), spacing=dp(12))
        self.total_label = MDLabel(
            text="Total: 0",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_SECONDARY),
            font_style="Caption",
        )
        stats.add_widget(self.total_label)
        active_label = MDLabel(
            text="● Ativos",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.SUCCESS),
            font_style="Caption",
        )
        stats.add_widget(active_label)
        layout.add_widget(stats)

        # Content area
        self.content = MDBoxLayout(orientation="vertical", spacing=dp(8))
        layout.add_widget(self.content)

        # Loading spinner
        self.spinner = MDSpinner(size=(dp(48), dp(48)), active=False)
        layout.add_widget(self.spinner)

        # FAB
        fab = MDFloatingActionButton(
            icon="account-plus",
            theme_icon_color="Custom",
            icon_color=c.to_rgba(c.WHITE),
            md_bg_color=c.to_rgba(c.PRIMARY_PURPLE),
            pos_hint={"center_x": 0.92, "center_y": 0.08},
            on_release=self._show_create_dialog,
        )
        layout.add_widget(fab)

        self.add_widget(layout)

    def on_enter(self):
        """Carrega usuários ao entrar na tela."""
        Clock.schedule_once(lambda dt: self._load_users(), 0.3)

    def _load_users(self):
        """Carrega lista de usuários da API."""
        # Placeholder - would call API
        self.content.clear_widgets()
        c = FloraColors()

        # Sample data
        users = [
            {"name": "João Silva", "email": "@example.com", "plan": "Premium", "status": "active", "bots": 3},
            {"name": "Maria Santos", "email": "@test.com", "plan": "Pro", "status": "active", "bots": 1},
            {"name": "Pedro Costa", "email": "@demo.com", "plan": "Free", "status": "expired", "bots": 0},
        ]

        for user in users:
            card = MDCard(
                orientation="vertical",
                padding=dp(12),
                spacing=dp(4),
                size_hint_y=None,
                height=dp(100),
                radius=[FloraTheme.CARD_RADIUS],
                elevation=FloraTheme.CARD_ELEVATION,
                md_bg_color=c.to_rgba(c.SURFACE_CARD),
            )

            row = MDBoxLayout(spacing=dp(8))
            info = MDBoxLayout(orientation="vertical", spacing=dp(2))
            name_lbl = MDLabel(
                text=f"[b]{user['name']}[/b]",
                theme_text_color="Custom",
                text_color=c.to_rgba(c.TEXT_PRIMARY),
                markup=True,
                font_style="Body",
            )
            info.add_widget(name_lbl)

            email_lbl = MDLabel(
                text=user["email"],
                theme_text_color="Custom",
                text_color=c.to_rgba(c.TEXT_SECONDARY),
                font_style="Caption",
            )
            info.add_widget(email_lbl)

            plan_chip = MDChip(
                label=user["plan"],
                text_color=c.to_rgba(c.WHITE),
                md_bg_color=c.to_rgba(c.PRIMARY_PURPLE),
            )
            info.add_widget(plan_chip)
            row.add_widget(info)

            status_color = c.SUCCESS if user["status"] == "active" else c.ERROR
            status_chip = MDChip(
                label=user["status"].capitalize(),
                text_color=c.to_rgba(c.WHITE),
                md_bg_color=c.to_rgba(status_color),
            )
            row.add_widget(status_chip)
            card.add_widget(row)

            # Action buttons
            actions = MDBoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
            edit_btn = MDIconButton(icon="pencil", theme_icon_color="Custom",
                                    icon_color=c.to_rgba(c.ACCENT_PINK))
            delete_btn = MDIconButton(icon="delete", theme_icon_color="Custom",
                                      icon_color=c.to_rgba(c.ERROR))
            actions.add_widget(edit_btn)
            actions.add_widget(delete_btn)
            card.add_widget(actions)

            self.content.add_widget(card)

        self.total_label.text = f"Total: {len(users)}"

    def _on_search(self, instance):
        query = instance.text
        MDSnackbar(MDSnackbarText(text=f"Buscando: {query}")).open()

    def _show_filter(self, instance):
        MDSnackbar(MDSnackbarText(text="Filtros em desenvolvimento")).open()

    def _show_create_dialog(self, instance):
        c = FloraColors()
        content = MDBoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, height=dp(200))
        content.add_widget(MDTextField(hint_text="Nome completo", mode="rectangle",
                                       radius=[FloraTheme.INPUT_RADIUS]))
        content.add_widget(MDTextField(hint_text="Email", mode="rectangle",
                                       radius=[FloraTheme.INPUT_RADIUS]))
        content.add_widget(MDTextField(hint_text="Senha temporária", mode="rectangle",
                                       radius=[FloraTheme.INPUT_RADIUS], password=True))

        self.dialog = MDDialog(
            title="Novo Usuário",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", theme_text_color="Custom",
                             text_color=c.to_rgba(c.TEXT_SECONDARY)),
                MDFillRoundFlatButton(text="Criar", md_bg_color=c.to_rgba(c.PRIMARY_PURPLE),
                                      on_release=self._create_user),
            ],
        )
        self.dialog.open()

    def _create_user(self, instance):
        self.dialog.dismiss()
        MDSnackbar(MDSnackbarText(text="Usuário criado com sucesso!")).open()
