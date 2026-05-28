# ═══════════════════════════════════════════════════════════════
# Flora Platform — Profile Screen
# ═══════════════════════════════════════════════════════════════

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.divider import MDDivider


class ProfileScreen(MDScreen):
    """User profile display and edit screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        self.md_bg_color = (0.102, 0.102, 0.180, 1)

        layout = MDFloatLayout()

        # Top bar
        top_bar = MDBoxLayout(
            size_hint=(1, None),
            height=dp(56),
            pos_hint={"top": 1},
            padding=[dp(8), dp(4)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            elevation=4,
        )
        back_btn = MDIconButton(
            icon="arrow-left",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
            on_release=self._on_back,
        )
        top_bar.add_widget(back_btn)
        top_bar.add_widget(MDLabel(
            text="Meu Perfil 👤",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        ))
        layout.add_widget(top_bar)

        # Content
        scroll = MDScrollView(
            pos_hint={"top": 0.92},
            size_hint=(1, 0.92),
            do_scroll_x=False,
        )

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=[dp(16), dp(8), dp(16), dp(100)],
            size_hint_y=None,
            adaptive_height=True,
        )

        # ── Profile Header Card ────────────────────────
        header_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(160),
            radius=[dp(24)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(24), dp(20)],
            spacing=dp(8),
            elevation=4,
        )

        # Avatar
        avatar_box = MDBoxLayout(
            size_hint=(1, None),
            height=dp(64),
        )
        avatar_circle = MDCard(
            size_hint=(None, None),
            size=(dp(64), dp(64)),
            pos_hint={"center_x": 0.5},
            radius=[dp(32)],
            md_bg_color=(0.424, 0.388, 1.0, 0.3),
        )
        avatar_circle.add_widget(MDLabel(
            text="👤",
            font_size=sp(32),
            halign="center",
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        ))
        avatar_box.add_widget(avatar_circle)
        header_card.add_widget(avatar_box)

        # Name
        self.name_label = MDLabel(
            text="Usuaria",
            font_style="Headline",
            role="small",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )
        header_card.add_widget(self.name_label)

        # Email
        self.email_label = MDLabel(
            text="usuario@email.com",
            font_style="Body",
            role="medium",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        )
        header_card.add_widget(self.email_label)

        content.add_widget(header_card)

        # ── Account Info Card ──────────────────────────
        info_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(220),
            radius=[dp(20)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(20), dp(16)],
            spacing=dp(8),
            elevation=2,
        )

        info_card.add_widget(MDLabel(
            text="Informacoes da Conta",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
        ))

        info_card.add_widget(MDDivider())

        # Plan info
        info_card.add_widget(self._info_row("Plano", "Basico 🌿"))
        info_card.add_widget(self._info_row("Licenca", "****-****-XXXX-XXXX"))
        info_card.add_widget(self._info_row("Membro desde", "Maio 2026"))
        info_card.add_widget(self._info_row("Status", "Ativa ✅"))

        content.add_widget(info_card)

        # ── Stats Card ─────────────────────────────────
        stats_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(140),
            radius=[dp(20)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(20), dp(16)],
            spacing=dp(8),
            elevation=2,
        )

        stats_card.add_widget(MDLabel(
            text="Estatisticas",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
        ))

        stats_card.add_widget(MDDivider())

        stats_grid = MDBoxLayout(
            size_hint=(1, None),
            height=dp(60),
            spacing=dp(8),
        )

        for val, label in [("0", "Mensagens"), ("0", "Contatos"), ("0", "Dias Ativa")]:
            stat_box = MDBoxLayout(orientation="vertical")
            stat_box.add_widget(MDLabel(
                text=val,
                font_style="Title",
                role="large",
                halign="center",
                theme_text_color="Custom",
                text_color=(0.424, 0.388, 1.0, 1),
            ))
            stat_box.add_widget(MDLabel(
                text=label,
                font_style="Label",
                role="small",
                halign="center",
                theme_text_color="Custom",
                text_color=(0.7, 0.7, 0.75, 1),
            ))
            stats_grid.add_widget(stat_box)

        stats_card.add_widget(stats_grid)
        content.add_widget(stats_card)

        # ── Action Buttons ─────────────────────────────
        edit_btn = MDButton(
            MDButtonText(text="Editar Perfil"),
            style="filled",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=(0.424, 0.388, 1.0, 1),
            on_release=self._on_edit,
        )
        content.add_widget(edit_btn)

        pwd_btn = MDButton(
            MDButtonText(text="Alterar Senha"),
            style="outlined",
            size_hint=(1, None),
            height=dp(48),
            line_color=(0.424, 0.388, 1.0, 1),
            text_color=(0.424, 0.388, 1.0, 1),
            on_release=self._on_change_password,
        )
        content.add_widget(pwd_btn)

        logout_btn = MDButton(
            MDButtonText(text="Sair da Conta"),
            style="outlined",
            size_hint=(1, None),
            height=dp(48),
            line_color=(0.957, 0.263, 0.212, 1),
            text_color=(0.957, 0.263, 0.212, 1),
            on_release=self._on_logout,
        )
        content.add_widget(logout_btn)

        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def _info_row(self, label: str, value: str) -> MDBoxLayout:
        """Create an info row."""
        row = MDBoxLayout(
            size_hint=(1, None),
            height=dp(28),
            spacing=dp(8),
        )
        row.add_widget(MDLabel(
            text=label,
            font_style="Label",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
            size_hint_x=0.4,
        ))
        row.add_widget(MDLabel(
            text=value,
            font_style="Label",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_x=0.6,
            halign="right",
        ))
        return row

    def on_enter(self):
        """Load user data when entering."""
        self._load_user_data()

    def _load_user_data(self):
        """Load user data from storage."""
        from apps.client.main import get_stored_user, load_token_data
        user = get_stored_user()
        data = load_token_data()

        if user:
            self.name_label.text = user.get("name", "Usuaria")
            self.email_label.text = user.get("email", "usuario@email.com")

    def _on_edit(self, instance):
        """Edit profile."""
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            if app and hasattr(app, 'show_snackbar'):
                app.show_snackbar("Edicao de perfil em breve!", (0.424, 0.388, 1.0, 1))
        except Exception:
            pass

    def _on_change_password(self, instance):
        """Change password."""
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            if app and hasattr(app, 'show_snackbar'):
                app.show_snackbar("Alteracao de senha em breve!", (0.424, 0.388, 1.0, 1))
        except Exception:
            pass

    def _on_logout(self, instance):
        """Logout the user."""
        from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer

        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Sair da Conta"),
            MDDialogSupportingText(text="Tem certeza que deseja sair? Voce precisara de sua licenca para entrar novamente."),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Cancelar"),
                    style="text",
                    on_release=lambda x: self.dialog.dismiss(),
                ),
                MDButton(
                    MDButtonText(text="Sair"),
                    style="text",
                    theme_text_color="Custom",
                    text_color=(0.957, 0.263, 0.212, 1),
                    on_release=self._do_logout,
                ),
                spacing=dp(8),
            ),
        )
        self.dialog.open()

    def _do_logout(self, instance):
        """Perform logout."""
        self.dialog.dismiss()
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            if app:
                app.logout()
        except Exception:
            self.manager.current = "welcome"

    def _on_back(self, instance):
        self.manager.current = "dashboard"
