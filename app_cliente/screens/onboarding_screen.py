"""Onboarding Screen - Fluxo de boas-vindas."""
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard


class OnboardingScreen(MDScreen):
    """Tela de onboarding para novos usuários."""

    def on_enter(self):
        self.build_ui()

    def build_ui(self):
        from app_cliente.main import ThemeColors

        layout = MDBoxLayout(
            orientation="vertical",
            spacing=16,
            padding=32,
            md_bg_color=get_color_from_hex(ThemeColors.PRIMARY),
        )

        layout.add_widget(MDBoxLayout(size_hint_y=0.1))

        layout.add_widget(
            MDLabel(text="🎉 Bem-vindo à Flora!", font_style="H4", halign="center",
                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY))
        )
        layout.add_widget(
            MDLabel(text="Vamos configurar seu primeiro chatbot em 3 passos simples.",
                     font_style="Body2", halign="center",
                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY))
        )

        layout.add_widget(MDBoxLayout(size_hint_y=0.05))

        # Passos
        steps = [
            ("1", "Escolha seu plano", "Selecione o plano ideal para suas necessidades"),
            ("2", "Crie seu bot", "Configure a personalidade e comportamento"),
            ("3", "Conecte o WhatsApp", "Escaneie o QR code e comece a usar"),
        ]

        for num, title, desc in steps:
            card = MDCard(
                orientation="vertical", spacing=4, padding=16,
                size_hint=(1, None), height=100,
                md_bg_color=get_color_from_hex(ThemeColors.CARD), radius=[12], elevation=2,
            )
            card.add_widget(
                MDLabel(text=f"Passo {num}: {title}", font_style="Subtitle1",
                         theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.HIGHLIGHT))
            )
            card.add_widget(
                MDLabel(text=desc, font_style="Body2",
                         theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY))
            )
            layout.add_widget(card)

        layout.add_widget(MDBoxLayout())

        layout.add_widget(
            MDRaisedButton(
                text="COMEÇAR", size_hint=(1, None), height=48,
                md_bg_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                on_release=lambda x: setattr(self.manager, "current", "home"),
            )
        )

        self.clear_widgets()
        self.add_widget(layout)
