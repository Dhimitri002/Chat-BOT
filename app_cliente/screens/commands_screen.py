"""Commands Screen - Gerenciamento de comandos."""
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard


class CommandsScreen(MDScreen):
    """Tela de gerenciamento de comandos."""

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
        header.add_widget(MDLabel(text="Comandos", font_style="H6", theme_text_color="Custom",
                                   text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY)))
        header.add_widget(MDBoxLayout(size_hint_x=0.3))
        header.add_widget(MDIconButton(icon="plus", theme_text_color="Custom",
                                        text_color=get_color_from_hex(ThemeColors.HIGHLIGHT)))
        layout.add_widget(header)

        # Built-in commands
        builtins = [
            ("/help", "Mostra lista de comandos"),
            ("/menu", "Mostra menu"),
            ("/info", "Informações sobre o bot"),
            ("/transfer", "Transferir para humano"),
            ("/reset", "Reiniciar conversa"),
        ]

        layout.add_widget(MDLabel(text="Comandos Built-in", font_style="Subtitle2", size_hint_y=None, height=30,
                                   theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY)))

        for trigger, desc in builtins:
            card = MDCard(orientation="horizontal", spacing=12, padding=12, size_hint_y=None, height=56,
                           md_bg_color=get_color_from_hex(ThemeColors.CARD), radius=[8], elevation=1)
            card.add_widget(MDLabel(text=trigger, font_style="Subtitle2", size_hint_x=0.3,
                                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.HIGHLIGHT)))
            card.add_widget(MDLabel(text=desc, font_style="Body2", size_hint_x=0.7,
                                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY)))
            layout.add_widget(card)

        layout.add_widget(MDBoxLayout())
        self.clear_widgets()
        self.add_widget(layout)
