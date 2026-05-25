"""
ConfirmationModal — Reusable modal dialog for confirmations / alerts.

Usage:
    modal = ConfirmationModal(
        title="Excluir bot",
        message="Tem certeza que deseja excluir este bot?",
        on_confirm=lambda: delete_bot(),
    )
    modal.open()
"""
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivy.uix.modalview import ModalView

from app_admin.utils.constants import Colors
from app_admin.styles.theme import Theme


class ConfirmationModal(ModalView):
    """Modal centered dialog with title, message, confirm & cancel buttons."""

    title = StringProperty("Confirmar")
    message = StringProperty("")
    confirm_text = StringProperty("Confirmar")
    cancel_text = StringProperty("Cancelar")
    confirm_color = ListProperty(Colors.ERROR)
    on_confirm = ObjectProperty(None)   # callback()
    on_cancel = ObjectProperty(None)    # callback()

    def __init__(self, **kwargs):
        super().__init__(
            size_hint=(0.6, None),
            height=dp(220),
            auto_dismiss=True,
            background_color=(0, 0, 0, 0.5),
            **kwargs,
        )
        self._build()

    def _build(self):
        card = MDCard(
            orientation="vertical",
            padding=Theme.SPACE_XL,
            spacing=Theme.SPACE_MD,
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_XL],
            elevation=Theme.ELEVATION_MODAL,
        )

        # Title
        self._title_label = MDLabel(
            text=self.title,
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            halign="center",
            size_hint_y=None,
            height=dp(28),
            shorten=True,
        )
        card.add_widget(self._title_label)

        # Divider
        divider = MDBoxLayout(size_hint_y=None, height=dp(1), md_bg_color=Colors.BG_INPUT)
        card.add_widget(divider)

        # Message
        self._msg_label = MDLabel(
            text=self.message,
            font_style="Body2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            halign="center",
            valign="top",
            markup=True,
        )
        self._msg_label.bind(size=self._msg_label.setter("text_size"))
        card.add_widget(self._msg_label)

        # Buttons row
        buttons = MDBoxLayout(
            orientation="horizontal",
            spacing=Theme.SPACE_MD,
            size_hint_y=None,
            height=dp(40),
            padding=[Theme.SPACE_XL, 0],
        )

        cancel_btn = MDFlatButton(
            text=self.cancel_text,
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            on_release=lambda x: self._do_cancel(),
        )
        buttons.add_widget(cancel_btn)

        spacer = MDBoxLayout()
        buttons.add_widget(spacer)

        confirm_btn = MDRaisedButton(
            text=self.confirm_text,
            md_bg_color=self.confirm_color,
            text_color=Colors.TEXT_PRIMARY,
            radius=[Theme.RADIUS_MEDIUM],
            elevation=Theme.ELEVATION_LOW,
            on_release=lambda x: self._do_confirm(),
        )
        buttons.add_widget(confirm_btn)

        card.add_widget(buttons)
        self.add_widget(card)

    def open(self, *args, **kwargs):
        self._title_label.text = self.title
        self._msg_label.text = self.message
        super().open(*args, **kwargs)
        # Subtle scale animation
        card = self.children[0]
        card.scale = 0.9
        Animation(scale=1.0, duration=Theme.Anim.NORMAL).start(card)

    def _do_confirm(self):
        self.dismiss()
        if self.on_confirm:
            self.on_confirm()

    def _do_cancel(self):
        self.dismiss()
        if self.on_cancel:
            self.on_cancel()

    def on_title(self, _inst, val):
        if hasattr(self, "_title_label"):
            self._title_label.text = val

    def on_message(self, _inst, val):
        if hasattr(self, "_msg_label"):
            self._msg_label.text = val
