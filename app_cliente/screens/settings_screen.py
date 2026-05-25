"""Settings Screen — Tela de configuracoes do perfil."""
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDSwitch
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
# from kivymd.uix.divider import MDDivider  # reserved for future use


class SettingsScreen(MDScreen):
    """Tela de configuracoes do usuario."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "settings"
        self.build()

    def build(self):
        from app_cliente.main import ThemeColors

        root = MDBoxLayout(
            orientation="vertical",
            md_bg_color=get_color_from_hex(ThemeColors.PRIMARY),
        )
        self.add_widget(root)

        # ---- Top Bar ----
        top_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=dp(12),
            spacing=dp(8),
            md_bg_color=get_color_from_hex(ThemeColors.SECONDARY),
        )

        back_btn = MDFlatButton(
            text="←",
            font_size="24sp",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_x=None,
            width=dp(48),
        )
        back_btn.bind(on_release=self._go_back)
        top_bar.add_widget(back_btn)

        top_bar.add_widget(MDLabel(
            text="⚙️ Configuracoes",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            bold=True,
        ))
        root.add_widget(top_bar)

        # ---- Content ----
        scroll = MDScrollView()
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=dp(16),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))
        scroll.add_widget(content)
        root.add_widget(scroll)

        # ---- Profile Section ----
        profile_card = MDCard(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(20),
            radius=[16],
            elevation=3,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
            height=dp(180),
        )

        profile_card.add_widget(MDLabel(
            text="Perfil",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        ))

        # Avatar row
        avatar_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(56),
        )
        avatar_circle = MDLabel(
            text="👤",
            font_style="H4",
            size_hint_x=None,
            width=dp(48),
            halign="center",
        )
        avatar_row.add_widget(avatar_circle)

        name_box = MDBoxLayout(orientation="vertical", spacing=dp(2))
        self.name_label = MDLabel(
            text="Usuario",
            font_style="Subtitle1",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(24),
            bold=True,
        )
        self.email_label = MDLabel(
            text="usuario@email.com",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
            size_hint_y=None,
            height=dp(18),
        )
        name_box.add_widget(self.name_label)
        name_box.add_widget(self.email_label)
        avatar_row.add_widget(name_box)
        profile_card.add_widget(avatar_row)

        edit_btn = MDRaisedButton(
            text="Editar Perfil",
            md_bg_color=get_color_from_hex(ThemeColors.ACCENT),
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint=(None, None),
            size_hint_y=None,
            height=dp(36),
            radius=[12],
        )
        edit_btn.bind(on_release=self._edit_profile)
        profile_card.add_widget(edit_btn)

        content.add_widget(profile_card)

        # ---- Notifications Section ----
        notif_card = MDCard(
            orientation="vertical",
            spacing=dp(4),
            padding=dp(16),
            radius=[16],
            elevation=2,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
        )
        notif_card.bind(minimum_height=notif_card.setter("height"))

        notif_card.add_widget(MDLabel(
            text="Notificacoes",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        ))

        # Notification toggles
        toggle_data = [
            ("Notificacoes push", "Receba alertas em tempo real", True),
            ("Notificacoes por email", "Relatorios diarios", False),
            ("Alertas de erro", "Seu bot parou? Avise-me!", True),
            ("Novidades", "Updates e novos recursos", False),
        ]

        for title_text, desc_text, default_val in toggle_data:
            toggle_row = self._create_toggle_row(title_text, desc_text, default_val)
            notif_card.add_widget(toggle_row)

        content.add_widget(notif_card)

        # ---- Preferences Section ----
        pref_card = MDCard(
            orientation="vertical",
            spacing=dp(4),
            padding=dp(16),
            radius=[16],
            elevation=2,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
        )
        pref_card.bind(minimum_height=pref_card.setter("height"))

        pref_card.add_widget(MDLabel(
            text="Preferencias",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        ))

        # Language
        lang_row = self._preference_row("Idioma", "🇧🇷 Portugues (BR)", self._on_language)
        pref_card.add_widget(lang_row)

        # Theme
        theme_row = self._preference_row("Tema", "🌙 Escuro Premium", self._on_theme)
        pref_card.add_widget(theme_row)

        content.add_widget(pref_card)

        # ---- License Section ----
        license_card = MDCard(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(16),
            radius=[16],
            elevation=2,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
            height=dp(120),
        )

        license_card.add_widget(MDLabel(
            text="Licenca",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        ))

        self.license_label = MDLabel(
            text="Plano: Gratuito",
            font_style="Body1",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(24),
        )
        license_card.add_widget(self.license_label)

        self.license_expiry_label = MDLabel(
            text="Validade: Sem limite",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
            size_hint_y=None,
            height=dp(18),
        )
        license_card.add_widget(self.license_expiry_label)
        content.add_widget(license_card)

        # ---- About Section ----
        about_card = MDCard(
            orientation="vertical",
            spacing=dp(4),
            padding=dp(16),
            radius=[16],
            elevation=2,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
            height=dp(120),
        )

        about_card.add_widget(MDLabel(
            text="Sobre",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        ))
        about_card.add_widget(MDLabel(
            text="Flora Platform v1.0.0",
            font_style="Body1",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(24),
        ))
        about_card.add_widget(MDLabel(
            text="Feito com amor para automatizar o WhatsApp",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
            size_hint_y=None,
            height=dp(18),
        ))

        # Version status
        about_card.add_widget(MDLabel(
            text="Ultima versao disponivel",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.SUCCESS),
            size_hint_y=None,
            height=dp(16),
        ))
        content.add_widget(about_card)

        # ---- Logout Button ----
        logout_btn = MDRaisedButton(
            text="🚪 Sair da Conta",
            md_bg_color=get_color_from_hex(ThemeColors.ERROR),
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            font_size="16sp",
            radius=[12],
            size_hint_y=None,
            height=dp(48),
        )
        logout_btn.bind(on_release=self._logout)
        content.add_widget(logout_btn)

        content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(20)))

    def _create_toggle_row(self, title, description, default):
        """Cria uma linha com toggle switch."""
        from app_cliente.main import ThemeColors
        row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(44),
        )

        text_box = MDBoxLayout(orientation="vertical", spacing=dp(0))
        text_box.add_widget(MDLabel(
            text=title,
            font_style="Body1",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(22),
        ))
        text_box.add_widget(MDLabel(
            text=description,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
            size_hint_y=None,
            height=dp(16),
        ))
        row.add_widget(text_box)

        switch = MDSwitch(
            active=default,
        )
        switch.active = default
        row.add_widget(switch)

        return row

    def _preference_row(self, label, value, callback):
        """Cria uma linha de preferencia clicavel."""
        from app_cliente.main import ThemeColors
        row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(44),
        )
        row.add_widget(MDLabel(
            text=label,
            font_style="Body1",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
        ))
        row.add_widget(MDLabel(text=""))
        btn = MDFlatButton(
            text=f"{value}  →",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_x=None,
        )
        btn.bind(on_release=callback)
        row.add_widget(btn)
        return row

    def _edit_profile(self, *args):
        """Editar perfil."""
        pass

    def _on_language(self, *args):
        """Selecionar idioma."""
        pass

    def _on_theme(self, *args):
        """Selecionar tema."""
        pass

    def _logout(self, *args):
        """Fazer logout."""
        from app_cliente.services.api_client import api
        api.clear_token()
        app = self.manager.parent
        app.is_authenticated = False
        app.user_name = "Usuario"
        app.user_email = ""
        app.user_plan = "Gratuito"
        self.manager.transition.direction = "right"
        self.manager.current = "login"

    def _go_back(self, *args):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_enter(self):
        app = self.manager.parent
        if app:
            self.name_label.text = app.user_name or "Usuario"
            self.email_label.text = app.user_email or "usuario@email.com"
            self.license_label.text = f"Plano: {app.user_plan or 'Gratuito'}"
