"""Chat Screen - Interface de chat."""
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField


class ChatScreen(MDScreen):
    """Tela de chat."""

    def on_enter(self):
        self.build_ui()

    def build_ui(self):
        from app_cliente.main import ThemeColors

        layout = MDBoxLayout(orientation="vertical", spacing=8, padding=8,
                              md_bg_color=get_color_from_hex(ThemeColors.PRIMARY))

        header = MDBoxLayout(size_hint_y=None, height=50, spacing=8)
        header.add_widget(MDIconButton(icon="arrow-left", theme_text_color="Custom",
                                        text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
                                        on_release=lambda x: setattr(self.manager, "current", "home")))
        header.add_widget(MDLabel(text="Conversas", font_style="H6", theme_text_color="Custom",
                                   text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY)))
        layout.add_widget(header)

        empty = MDCard(orientation="vertical", spacing=8, padding=32,
                        md_bg_color=get_color_from_hex(ThemeColors.CARD), radius=[12], elevation=2)
        empty.add_widget(MDLabel(text="💬", font_style="H2", halign="center"))
        empty.add_widget(MDLabel(text="Nenhuma conversa ainda", font_style="Subtitle1", halign="center",
                                  theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY)))
        empty.add_widget(MDLabel(text="Conecte seu WhatsApp para começar a receber mensagens!",
                                  font_style="Body2", halign="center",
                                  theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY)))
        layout.add_widget(empty)

        layout.add_widget(MDBoxLayout())
        self.clear_widgets()
        self.add_widget(layout)
