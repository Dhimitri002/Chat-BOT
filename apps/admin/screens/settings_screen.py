"""
Flora Admin — Tela de Configurações
======================================
Configurações do sistema: perfil admin, API keys, provedores LLM,
notificações e informações do sistema.
"""

from kivy.metrics import dp

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.switch import MDSwitch
from kivymd.uix.textfield import MDTextField
from apps.shared.theme import FloraColors, FloraTheme


class SettingsScreen(MDScreen):
    """Tela de configurações administrativas."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self._build_ui()

    def _build_ui(self):
        c = FloraColors()
        layout = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        # Header
        header = MDBoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        title = MDLabel(
            text="⚙️  Configurações",
            font_style="H4",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
            bold=True,
        )
        header.add_widget(title)
        layout.add_widget(header)

        # ── Admin Profile ──
        profile_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            radius=[FloraTheme.CARD_RADIUS],
            elevation=FloraTheme.CARD_ELEVATION,
            md_bg_color=c.to_rgba(c.SURFACE_CARD),
        )
        profile_card.add_widget(MDLabel(
            text="[b]👤 Perfil do Admin[/b]",
            font_style="H5",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
            markup=True,
        ))
        profile_card.add_widget(MDTextField(
            hint_text="Nome",
            text="Administrador",
            mode="rectangle",
            radius=[FloraTheme.INPUT_RADIUS],
        ))
        profile_card.add_widget(MDTextField(
            hint_text="Email",
            text="@flora.com",
            mode="rectangle",
            radius=[FloraTheme.INPUT_RADIUS],
        ))
        profile_card.add_widget(MDFillRoundFlatButton(
            text="Salvar Perfil",
            md_bg_color=c.to_rgba(c.PRIMARY_PURPLE),
            on_release=self._save_profile,
        ))
        layout.add_widget(profile_card)

        # ── LLM Providers ──
        llm_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            radius=[FloraTheme.CARD_RADIUS],
            elevation=FloraTheme.CARD_ELEVATION,
            md_bg_color=c.to_rgba(c.SURFACE_CARD),
        )
        llm_card.add_widget(MDLabel(
            text="[b]🤖 Provedores LLM[/b]",
            font_style="H5",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
            markup=True,
        ))

        for provider in ["OpenAI", "Anthropic (Claude)", "Groq", "Google (Gemini)", "Ollama"]:
            row = MDBoxLayout(size_hint_y=None, height=dp(40), spacing=dp(12))
            row.add_widget(MDLabel(
                text=provider,
                theme_text_color="Custom",
                text_color=c.to_rgba(c.TEXT_PRIMARY),
                font_style="Body",
                size_hint_x=0.6,
            ))
            switch = MDSwitch(
                size_hint_x=0.2,
                pos_hint={"center_y": 0.5},
            )
            row.add_widget(switch)
            api_btn = MDIconButton(
                icon="key-variant",
                theme_icon_color="Custom",
                icon_color=c.to_rgba(c.ACCENT_PINK),
                size_hint_x=0.2,
            )
            row.add_widget(api_btn)
            llm_card.add_widget(row)

        layout.add_widget(llm_card)

        # ── Security Settings ──
        security_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            radius=[FloraTheme.CARD_RADIUS],
            elevation=FloraTheme.CARD_ELEVATION,
            md_bg_color=c.to_rgba(c.SURFACE_CARD),
        )
        security_card.add_widget(MDLabel(
            text="[b]🔒 Segurança[/b]",
            font_style="H5",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
            markup=True,
        ))

        # Token expiry
        token_row = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        token_row.add_widget(MDLabel(
            text="Expiração do token (horas)",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
        ))
        token_row.add_widget(MDTextField(
            text="24",
            mode="rectangle",
            radius=[FloraTheme.INPUT_RADIUS],
            size_hint_x=0.3,
            input_filter="int",
        ))
        security_card.add_widget(token_row)

        # Rate limit
        rate_row = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        rate_row.add_widget(MDLabel(
            text="Rate limit (req/min)",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
        ))
        rate_row.add_widget(MDTextField(
            text="60",
            mode="rectangle",
            radius=[FloraTheme.INPUT_RADIUS],
            size_hint_x=0.3,
            input_filter="int",
        ))
        security_card.add_widget(rate_row)

        security_card.add_widget(MDFillRoundFlatButton(
            text="Rotacionar Chaves API",
            md_bg_color=c.to_rgba(c.WARNING),
            on_release=self._rotate_keys,
        ))
        layout.add_widget(security_card)

        # ── System Info ──
        sys_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(4),
            radius=[FloraTheme.CARD_RADIUS],
            elevation=FloraTheme.CARD_ELEVATION,
            md_bg_color=c.to_rgba(c.SURFACE_CARD),
        )
        sys_card.add_widget(MDLabel(
            text="[b]ℹ️ Sistema[/b]",
            font_style="H5",
            theme_text_color="Custom",
            text_color=c.to_rgba(c.TEXT_PRIMARY),
            markup=True,
        ))
        for info in [
            "Versão: 1.0.0",
            "Python: 3.12",
            "FastAPI: 0.115.x",
            "Database: SQLite",
            "Uptime: 3 dias, 14 horas",
        ]:
            sys_card.add_widget(MDLabel(
                text=f"  • {info}",
                theme_text_color="Custom",
                text_color=c.to_rgba(c.TEXT_SECONDARY),
                font_style="Caption",
            ))
        layout.add_widget(sys_card)

        # ── Logout ──
        logout_btn = MDFillRoundFlatButton(
            text="🚪  Sair da Conta",
            md_bg_color=c.to_rgba(c.ERROR),
            size_hint_y=None,
            height=dp(48),
            on_release=self._logout,
        )
        layout.add_widget(logout_btn)

        # Bottom spacing
        layout.add_widget(MDBoxLayout(size_hint_y=None, height=dp(80)))

        self.add_widget(layout)

    def _save_profile(self, instance):
        MDSnackbar(MDSnackbarText(text="Perfil salvo com sucesso!")).open()

    def _rotate_keys(self, instance):
        MDSnackbar(MDSnackbarText(text="Chaves API rotacionadas com sucesso! 🔑")).open()

    def _logout(self, instance):
        """Faz logout do admin."""
        app = self.manager.parent
        if app and hasattr(app, 'logout'):
            app.logout()
        else:
            self.manager.current = "login"
