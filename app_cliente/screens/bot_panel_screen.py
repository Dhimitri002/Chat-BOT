"""Bot Panel Screen - Painel de controle do bot."""
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard


class BotPanelScreen(MDScreen):
    """Painel de controle do bot."""

    def on_enter(self):
        self.build_ui()

    def build_ui(self):
        from app_cliente.main import ThemeColors

        layout = MDBoxLayout(orientation="vertical", spacing=12, padding=16,
                              md_bg_color=get_color_from_hex(ThemeColors.PRIMARY))

        header = MDBoxLayout(size_hint_y=None, height=50, spacing=8)
        header.add_widget(MDIconButton(icon="arrow-left", theme_text_color="Custom",
                                        text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
                                        on_release=lambda x: setattr(self.manager, "current", "home")))
        header.add_widget(MDLabel(text="Meus Bots", font_style="H6", theme_text_color="Custom",
                                   text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY)))
        header.add_widget(MDBoxLayout(size_hint_x=0.3))
        header.add_widget(MDIconButton(icon="plus", theme_text_color="Custom",
                                        text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                                        on_release=lambda x: setattr(self.manager, "current", "bot_create")))
        layout.add_widget(header)

        # Empty state
        empty_card = MDCard(orientation="vertical", spacing=12, padding=32,
                             md_bg_color=get_color_from_hex(ThemeColors.CARD), radius=[12], elevation=2)
        empty_card.add_widget(MDLabel(text="🤖", font_style="H2", halign="center"))
        empty_card.add_widget(MDLabel(text="Nenhum bot criado ainda", font_style="Subtitle1", halign="center",
                                       theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY)))
        empty_card.add_widget(MDLabel(text="Crie seu primeiro chatbot WhatsApp!", font_style="Body2", halign="center",
                                       theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY)))
        empty_card.add_widget(MDBoxLayout(size_hint_y=None, height=10))
        empty_card.add_widget(
            MDRaisedButton(text="CRIAR MEU PRIMEIRO BOT", size_hint=(0.8, None), height=44,
                            md_bg_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                            pos_hint={"center_x": 0.5},
                            on_release=lambda x: setattr(self.manager, "current", "bot_create"))
        )
        layout.add_widget(empty_card)

        layout.add_widget(MDBoxLayout())
        self.clear_widgets()
        self.add_widget(layout)
