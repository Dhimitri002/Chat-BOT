# ═══════════════════════════════════════════════════════════════
# Flora Platform — Settings Screen
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
from kivymd.uix.switch import MDSwitch
from kivymd.uix.divider import MDDivider


class SettingsScreen(MDScreen):
    """App settings screen."""

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
            text="Configuracoes ⚙️",
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

        # ── Appearance Section ─────────────────────────
        content.add_widget(MDLabel(
            text="Aparencia",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            size_hint_y=None,
            height=dp(32),
        ))

        appearance_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(120),
            radius=[dp(16)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(16), dp(12)],
            spacing=dp(4),
            elevation=2,
        )

        # Dark mode toggle
        dark_row = self._toggle_row("Modo Escuro", "🌙", True)
        appearance_card.add_widget(dark_row)

        # Language selector
        lang_row = MDBoxLayout(
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(8),
        )
        lang_row.add_widget(MDLabel(
            text="🌐",
            font_size=sp(20),
            size_hint_x=0.1,
        ))
        lang_row.add_widget(MDLabel(
            text="Idioma",
            font_style="Body",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_x=0.6,
        ))
        lang_row.add_widget(MDLabel(
            text="Portugues 🇧🇷",
            font_style="Body",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            size_hint_x=0.3,
            halign="right",
        ))
        appearance_card.add_widget(lang_row)

        content.add_widget(appearance_card)

        # ── Notifications Section ──────────────────────
        content.add_widget(MDLabel(
            text="Notificacoes",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            size_hint_y=None,
            height=dp(32),
        ))

        notif_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(160),
            radius=[dp(16)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(16), dp(12)],
            spacing=dp(4),
            elevation=2,
        )

        notif_card.add_widget(self._toggle_row("Mensagens novas", "💬", True))
        notif_card.add_widget(self._toggle_row("Status do bot", "🤖", True))
        notif_card.add_widget(self._toggle_row("Alertas de licenca", "🔑", True))
        notif_card.add_widget(self._toggle_row("Dicas da Flora", "🌸", False))

        content.add_widget(notif_card)

        # ── API Section ────────────────────────────────
        content.add_widget(MDLabel(
            text="API",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            size_hint_y=None,
            height=dp(32),
        ))

        api_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(80),
            radius=[dp(16)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(16), dp(12)],
            spacing=dp(4),
            elevation=2,
        )

        api_card.add_widget(MDLabel(
            text="URL da API",
            font_style="Label",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        ))

        self.api_url_input = MDTextField(
            mode="outlined",
            text="http://localhost:8000/api/v1",
            line_color_focus=(0.424, 0.388, 1.0, 1),
            line_color_normal=(0.3, 0.3, 0.4, 1),
            text_color_normal=(0.7, 0.7, 0.75, 1),
            text_color_focus=(1, 1, 1, 1),
            fill_color_normal=(0.1, 0.1, 0.16, 1),
            size_hint_y=None,
            height=dp(48),
        )
        api_card.add_widget(self.api_url_input)

        content.add_widget(api_card)

        # ── About Section ──────────────────────────────
        content.add_widget(MDLabel(
            text="Sobre",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            size_hint_y=None,
            height=dp(32),
        ))

        about_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(140),
            radius=[dp(16)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(20), dp(16)],
            spacing=dp(6),
            elevation=2,
        )

        about_card.add_widget(MDLabel(
            text="🌸 Flora Platform",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        ))
        about_card.add_widget(MDLabel(
            text="Versao 0.1.0 (Beta)",
            font_style="Body",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        ))
        about_card.add_widget(MDLabel(
            text="Feito com amor pela ZOO Company",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 0.55, 1),
        ))
        about_card.add_widget(MDLabel(
            text="2026 Flora Platform. Todos os direitos reservados.",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.4, 0.4, 0.45, 1),
        ))

        content.add_widget(about_card)

        # ── Logout Button ──────────────────────────────
        content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(8)))

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

    def _toggle_row(self, label: str, emoji: str, default: bool) -> MDBoxLayout:
        """Create a toggle row."""
        row = MDBoxLayout(
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(8),
        )
        row.add_widget(MDLabel(
            text=emoji,
            font_size=sp(20),
            size_hint_x=0.1,
        ))
        row.add_widget(MDLabel(
            text=label,
            font_style="Body",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_x=0.65,
        ))
        switch = MDSwitch(
            active=default,
            pos_hint={"center_y": 0.5},
            thumb_color_active=(0.424, 0.388, 1.0, 1),
            thumb_color_inactive=(0.4, 0.4, 0.45, 1),
            track_color_active=(0.424, 0.388, 1.0, 0.3),
            track_color_inactive=(0.2, 0.2, 0.3, 1),
        )
        row.add_widget(switch)
        return row

    def _on_logout(self, instance):
        """Logout the user."""
        from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer

        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Sair da Conta"),
            MDDialogSupportingText(text="Tem certeza que deseja sair?"),
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
