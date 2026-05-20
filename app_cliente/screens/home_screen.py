"""Home Screen - Dashboard principal do cliente."""
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout


class HomeScreen(MDScreen):
    """Dashboard principal do cliente."""

    def on_enter(self):
        self.build_ui()

    def build_ui(self):
        from app_cliente.main import ThemeColors

        layout = MDBoxLayout(
            orientation="vertical",
            spacing=12,
            padding=16,
            md_bg_color=get_color_from_hex(ThemeColors.PRIMARY),
        )

        # Header
        header = MDBoxLayout(size_hint_y=None, height=60, spacing=8)
        header.add_widget(
            MDLabel(text="🌸 Flora", font_style="H5",
                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                     size_hint_x=0.7)
        )
        header.add_widget(
            MDIconButton(icon="bell-outline", theme_text_color="Custom",
                          text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY))
        )
        header.add_widget(
            MDIconButton(icon="cog-outline", theme_text_color="Custom",
                          text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
                          on_release=lambda x: setattr(self.manager, "current", "settings"))
        )
        layout.add_widget(header)

        # Stats cards
        stats_grid = MDGridLayout(cols=2, spacing=12, size_hint_y=None, height=220)

        stats = [
            ("🤖", "Bots Ativos", "0", ThemeColors.ACCENT),
            ("💬", "Msgs Hoje", "0", ThemeColors.SUCCESS),
            ("📱", "Conectados", "0", ThemeColors.HIGHLIGHT),
            ("⭐", "Plano", "Gratuito", ThemeColors.WARNING),
        ]

        for icon, label, value, color in stats:
            card = MDCard(
                orientation="vertical", spacing=4, padding=16,
                md_bg_color=get_color_from_hex(ThemeColors.CARD),
                radius=[12], elevation=2,
            )
            card.add_widget(MDLabel(text=icon, font_style="H4", halign="center"))
            card.add_widget(MDLabel(text=value, font_style="H6", halign="center",
                                     theme_text_color="Custom", text_color=get_color_from_hex(color)))
            card.add_widget(MDLabel(text=label, font_style="Caption", halign="center",
                                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY)))
            stats_grid.add_widget(card)

        layout.add_widget(stats_grid)

        # Quick actions
        layout.add_widget(
            MDLabel(text="Ações Rápidas", font_style="Subtitle1", size_hint_y=None, height=30,
                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY))
        )

        actions = MDBoxLayout(spacing=12, size_hint_y=None, height=50)
        actions.add_widget(
            MDRaisedButton(text="Criar Bot", icon="plus",
                           md_bg_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                           on_release=lambda x: setattr(self.manager, "current", "bot_create"))
        )
        actions.add_widget(
            MDRaisedButton(text="WhatsApp", icon="whatsapp",
                           md_bg_color=get_color_from_hex(ThemeColors.SUCCESS),
                           on_release=lambda x: setattr(self.manager, "current", "whatsapp"))
        )
        layout.add_widget(actions)

        # Recent activity
        layout.add_widget(
            MDLabel(text="Atividade Recente", font_style="Subtitle1", size_hint_y=None, height=30,
                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY))
        )

        activity_card = MDCard(
            orientation="vertical", spacing=8, padding=16,
            md_bg_color=get_color_from_hex(ThemeColors.CARD), radius=[12], elevation=2,
        )
        activity_card.add_widget(
            MDLabel(text="Nenhuma atividade ainda", font_style="Body2", halign="center",
                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_HINT))
        )
        activity_card.add_widget(
            MDLabel(text="Crie seu primeiro bot para começar!", font_style="Caption", halign="center",
                     theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_HINT))
        )
        layout.add_widget(activity_card)

        # Bottom nav placeholder
        layout.add_widget(MDBoxLayout())
        bottom_nav = MDBoxLayout(size_hint_y=None, height=60, spacing=0,
                                  md_bg_color=get_color_from_hex(ThemeColors.SURFACE))
        for icon_name, label, screen in [("home", "Início", "home"), ("robot", "Bots", "bot_panel"),
                                           ("whatsapp", "WhatsApp", "whatsapp"), ("cog", "Config", "settings")]:
            btn = MDBoxLayout(orientation="vertical", spacing=2)
            btn.add_widget(MDIconButton(icon=icon_name, theme_text_color="Custom",
                                         text_color=get_color_from_hex(ThemeColors.HIGHLIGHT if screen == "home" else ThemeColors.TEXT_SECONDARY),
                                         on_release=lambda x, s=screen: setattr(self.manager, "current", s)))
            btn.add_widget(MDLabel(text=label, font_style="Caption", halign="center",
                                    theme_text_color="Custom", text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY)))
            bottom_nav.add_widget(btn)
        layout.add_widget(bottom_nav)

        self.clear_widgets()
        self.add_widget(layout)
