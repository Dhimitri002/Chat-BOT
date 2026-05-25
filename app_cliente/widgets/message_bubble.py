"""Message Bubble - Bolha de mensagem para chat."""
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDIcon


class MessageBubble(MDCard):
    """Bolha de mensagem de chat com suporte a enviada/recebida."""

    def __init__(self, text: str, is_sent: bool = True, timestamp: str = "",
                 sender_name: str = "", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(12)
        self.spacing = dp(4)
        self.size_hint_y = None
        self.width = dp(260)
        self.is_sent = is_sent
        radius_val = [18, 18, 4, 18] if is_sent else [18, 18, 18, 4]

        from app_cliente.main import ThemeColors

        bg_color = ThemeColors.HIGHLIGHT if is_sent else ThemeColors.SECONDARY
        text_color = ThemeColors.TEXT_PRIMARY

        self.md_bg_color = get_color_from_hex(bg_color)
        self.radius = radius_val
        self.elevation = 1

        # Alinhamento
        align_box = MDBoxLayout(orientation="vertical", spacing=dp(2),
                                 size_hint_y=None)
        align_box.bind(minimum_height=align_box.setter("height"))

        # Nome do remetente (para mensagens recebidas em grupo)
        if sender_name and not is_sent:
            name_label = MDLabel(
                text=sender_name,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.SUCCESS),
                size_hint_y=None,
                height=dp(16),
                bold=True,
            )
            align_box.add_widget(name_label)
            align_box.height += dp(18)

        # Texto da mensagem
        msg_label = MDLabel(
            text=text,
            font_style="Body1",
            theme_text_color="Custom",
            text_color=get_color_from_hex(text_color),
            size_hint_y=None,
            text_size=(dp(240), None),
        )
        msg_label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", val[1] + dp(4))
        )
        align_box.add_widget(msg_label)
        align_box.height += msg_label.height + dp(4)

        # Timestamp
        if timestamp:
            time_label = MDLabel(
                text=timestamp,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
                size_hint_y=None,
                height=dp(14),
                halign="right" if is_sent else "left",
            )
            align_box.add_widget(time_label)
            align_box.height += dp(16)

        self.add_widget(align_box)
        self.height = align_box.height + dp(24)
