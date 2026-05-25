"""Plan Card - Cartao de plano para tela de planos."""
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout


class PlanCard(MDCard):
    """Cartao que exibe informacoes de um plano."""

    def __init__(self, name: str = "", price: str = "R$ 0/mes",
                 features: list = None, is_current: bool = False,
                 is_popular: bool = False, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(10)
        self.padding = dp(20)
        self.radius = [16]
        self.elevation = 6 if is_current else 2
        self.size_hint_y = None
        self.size_hint_x = 0.9
        self.pos_hint = {"center_x": 0.5}

        from app_cliente.main import ThemeColors

        if is_current:
            self.md_bg_color = get_color_from_hex(ThemeColors.ACCENT)
        else:
            self.md_bg_color = get_color_from_hex(ThemeColors.CARD)

        # Plan name and badge
        name_row = MDBoxLayout(size_hint_y=None, height=dp(32))
        name_label = MDLabel(
            text=name,
            font_style="H5",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            bold=True,
        )
        name_row.add_widget(name_label)

        if is_popular:
            popular_label = MDLabel(
                text="  Mais Popular  ",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.WARNING),
                bold=True,
            )
            name_row.add_widget(popular_label)
        elif is_current:
            current_label = MDLabel(
                text="  Seu Plano Atual  ",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.SUCCESS),
                bold=True,
            )
            name_row.add_widget(current_label)
        else:
            name_row.add_widget(MDLabel(text=""))

        self.add_widget(name_row)

        # Price
        price_label = MDLabel(
            text=price,
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(30),
        )
        self.add_widget(price_label)

        # Divider
        divider = MDBoxLayout(
            size_hint_y=None,
            height=dp(1),
            md_bg_color=get_color_from_hex(ThemeColors.DIVIDER),
        )
        self.add_widget(divider)

        # Features
        content_height = dp(80)
        if features:
            for feat in features:
                feat_box = MDBoxLayout(
                    size_hint_y=None,
                    height=dp(28),
                    spacing=dp(4),
                )
                check_label = MDLabel(
                    text="OK",
                    font_style="Body2",
                    theme_text_color="Custom",
                    text_color=get_color_from_hex(ThemeColors.SUCCESS),
                    size_hint_x=None,
                    width=dp(30),
                    bold=True,
                )
                feat_label = MDLabel(
                    text=feat,
                    font_style="Body2",
                    theme_text_color="Custom",
                    text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
                )
                feat_box.add_widget(check_label)
                feat_box.add_widget(feat_label)
                self.add_widget(feat_box)
                content_height += dp(28)

        # Button
        btn = MDRaisedButton(
            text="Plano Atual" if is_current else "Escolher Plano",
            md_bg_color=get_color_from_hex(
                ThemeColors.SUCCESS if is_current else ThemeColors.HIGHLIGHT
            ),
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint=(None, None),
            size_hint_y=None,
            height=dp(44),
            pos_hint={"center_x": 0.5},
            disabled=is_current,
        )
        if on_select and not is_current:
            btn.bind(on_release=on_select)
        self.add_widget(btn)

        self.height = content_height + dp(120)
