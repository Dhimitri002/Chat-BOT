"""WhatsApp Screen - Conexão WhatsApp."""
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.spinner import MDSpinner


class WhatsAppScreen(MDScreen):
    """Tela de conexão WhatsApp."""

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
        header.add_widget(MDLabel(text="WhatsApp", font_style="H6", theme_text_color="Custom",
                                   text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY)))
        layout.add_widget(header)

        # Status card
        status_card = MDCard(orientation="vertical", spacing=12, padding=24,
                              md_bg_color=get_color_from_hex(ThemeColors.CARD), radius=[12], elevation=2)

        status_card.add_widget(MDLabel(text="📱", font_style="H2", halign="center"))
        status_card.add_widget(
            MDLabel(text="Desconectado", font_style="H6", halign="center",
                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.ERROR))
        )
        status_card.add_widget(
            MDLabel(text="Conecte seu WhatsApp para começar a receber e enviar mensagens.",
                     font_style="Body2", halign="center",
                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY))
        )

        layout.add_widget(status_card)

        # QR Code area
        qr_card = MDCard(orientation="vertical", spacing=8, padding=24,
                           md_bg_color=get_color_from_hex(ThemeColors.CARD), radius=[12], elevation=2)
        qr_card.add_widget(
            MDLabel(text="Clique em 'Conectar' para gerar o QR Code.", font_style="Body2", halign="center",
                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_HINT))
        )
        layout.add_widget(qr_card)

        layout.add_widget(MDBoxLayout())

        # Connect button
        layout.add_widget(
            MDRaisedButton(text="CONECTAR WHATSAPP", size_hint=(1, None), height=48,
                            md_bg_color=get_color_from_hex(ThemeColors.SUCCESS),
                            on_release=self._connect_whatsapp)
        )

        self.clear_widgets()
        self.add_widget(layout)

    def _connect_whatsapp(self, *args):
        """Inicia conexão WhatsApp."""
        from app_cliente.services.api_client import APIClient
        api = APIClient()
        result = api.connect_whatsapp(bot_id="default")
        # Atualizar UI com QR code
