"""Bot Create Screen - Tela de criação de bot."""
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard


class BotCreateScreen(MDScreen):
    """Tela de criação de novo bot."""

    def on_enter(self):
        self.build_ui()

    def build_ui(self):
        from app_cliente.main import ThemeColors

        layout = MDBoxLayout(orientation="vertical", spacing=12, padding=16,
                              md_bg_color=get_color_from_hex(ThemeColors.PRIMARY))

        # Header
        header = MDBoxLayout(size_hint_y=None, height=50, spacing=8)
        header.add_widget(MDIconButton(icon="arrow-left", theme_text_color="Custom",
                                        text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
                                        on_release=lambda x: setattr(self.manager, "current", "home")))
        header.add_widget(MDLabel(text="Criar Bot", font_style="H6", theme_text_color="Custom",
                                   text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY)))
        layout.add_widget(header)

        # Form
        form_card = MDCard(orientation="vertical", spacing=12, padding=20,
                            md_bg_color=get_color_from_hex(ThemeColors.CARD), radius=[12], elevation=2)

        self.name_field = MDTextField(hint_text="Nome do bot", icon_right="robot", mode="round")
        form_card.add_widget(self.name_field)

        self.purpose_field = MDTextField(hint_text="Propósito (ex: atendimento ao cliente)", icon_right="text", mode="round")
        form_card.add_widget(self.purpose_field)

        self.welcome_field = MDTextField(hint_text="Mensagem de boas-vindas", icon_right="message-text",
                                          mode="rectangle", multiline=True, size_hint_y=None, height=100)
        form_card.add_widget(self.welcome_field)

        layout.add_widget(form_card)

        # Templates
        layout.add_widget(MDLabel(text="Template", font_style="Subtitle2", size_hint_y=None, height=30,
                                   theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY)))

        templates = MDBoxLayout(spacing=8, size_hint_y=None, height=80)
        for icon, name in [("🤝", "Atendimento"), ("🛒", "Vendas"), ("🎯", "Suporte"), ("✨", "Personalizado")]:
            t_card = MDCard(orientation="vertical", spacing=4, padding=8,
                             md_bg_color=get_color_from_hex(ThemeColors.SURFACE), radius=[8])
            t_card.add_widget(MDLabel(text=icon, font_style="H5", halign="center"))
            t_card.add_widget(MDLabel(text=name, font_style="Caption", halign="center",
                                       theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY)))
            templates.add_widget(t_card)
        layout.add_widget(templates)

        layout.add_widget(MDBoxLayout())

        layout.add_widget(
            MDRaisedButton(text="CRIAR BOT", size_hint=(1, None), height=48,
                            md_bg_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                            on_release=self._create_bot)
        )

        self.clear_widgets()
        self.add_widget(layout)

    def _create_bot(self, *args):
        name = self.name_field.text.strip()
        if not name:
            return
        from app_cliente.services.api_client import APIClient
        api = APIClient()
        result = api.create_bot(name=name, purpose=self.purpose_field.text.strip(),
                                 welcome_message=self.welcome_field.text.strip())
        if result.get("success"):
            self.manager.current = "bot_panel"
        else:
            pass  # Show error
