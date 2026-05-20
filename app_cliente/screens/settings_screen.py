"""Settings Screen - Configurações do app."""
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard


class SettingsScreen(MDScreen):
    """Tela de configurações."""

    def on_enter(self):
        self.build_ui()

    def build_ui(self):
        from app_cliente.main import ThemeColors

        layout = MDBoxLayout(orientation="vertical", spacing=8, padding=16,
                              md_bg_color=get_color_from_hex(ThemeColors.PRIMARY))

        header = MDBoxLayout(size_hint_y=None, height=50, spacing=8)
        header.add_widget(MDIconButton(icon="arrow-left", theme_text_color="Custom",
                                        text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
                                        on_release=lambda x: setattr(self.manager, "current", "home")))
        header.add_widget(MDLabel(text="Configurações", font_style="H6", theme_text_color="Custom",
                                   text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY)))
        layout.add_widget(header)

        # Profile
        profile_card = MDCard(orientation="vertical", spacing=8, padding=16,
                               md_bg_color=get_color_from_hex(ThemeColors.CARD), radius=[12], elevation=2)
        profile_card.add_widget(MDLabel(text="👤 Perfil", font_style="Subtitle1",
                                         theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY)))
        profile_card.add_widget(MDLabel(text="Nome do Usuário", font_style="Body1",
                                         theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY)))
        profile_card.add_widget(MDLabel(text="email@exemplo.com", font_style="Caption",
                                         theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_HINT)))
        layout.add_widget(profile_card)

        # Subscription
        sub_card = MDCard(orientation="vertical", spacing=8, padding=16,
                            md_bg_color=get_color_from_hex(ThemeColors.CARD), radius=[12], elevation=2)
        sub_card.add_widget(MDLabel(text="⭐ Assinatura", font_style="Subtitle1",
                                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY)))
        sub_card.add_widget(MDLabel(text="Plano: Gratuito", font_style="Body1",
                                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.WARNING)))
        sub_card.add_widget(
            MDRaisedButton(text="FAZER UPGRADE", size_hint=(0.6, None), height=36,
                            md_bg_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                            pos_hint={"center_x": 0.5})
        )
        layout.add_widget(sub_card)

        # Settings options
        options = [
            ("🔔", "Notificações"),
            ("🌙", "Tema Escuro"),
            ("🌐", "Idioma"),
            ("🔒", "Privacidade"),
            ("❓", "Ajuda"),
        ]

        for icon, label in options:
            opt_card = MDCard(orientation="horizontal", spacing=12, padding=16, size_hint_y=None, height=52,
                                md_bg_color=get_color_from_hex(ThemeColors.CARD), radius=[8], elevation=1)
            opt_card.add_widget(MDLabel(text=icon, size_hint_x=0.15))
            opt_card.add_widget(MDLabel(text=label, font_style="Body1", size_hint_x=0.7,
                                         theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY)))
            opt_card.add_widget(MDLabel(text="›", font_style="H6", size_hint_x=0.15,
                                         theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_HINT)))
            layout.add_widget(opt_card)

        layout.add_widget(MDBoxLayout())

        # Logout
        layout.add_widget(
            MDRaisedButton(text="SAIR DA CONTA", size_hint=(1, None), height=44,
                            md_bg_color=get_color_from_hex(ThemeColors.ERROR),
                            on_release=self._logout)
        )

        self.clear_widgets()
        self.add_widget(layout)

    def _logout(self, *args):
        """Faz logout."""
        app = MDApp.get_running_app()
        app.logout()
