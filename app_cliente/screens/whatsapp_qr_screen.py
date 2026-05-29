# ═══════════════════════════════════════════════════════════════
# Flora Platform — WhatsApp QR Screen
# ═══════════════════════════════════════════════════════════════

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.graphics.texture import Texture

from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.progressindicator import MDCircularProgressIndicator, MDLinearProgressIndicator
from kivymd.uix.image import FitImage


class WhatsAppQrScreen(MDScreen):
    """QR code display screen for WhatsApp connection."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._refresh_event = None
        self._build_ui()

    def _build_ui(self):
        self.md_bg_color = (0.102, 0.102, 0.180, 1)

        layout = MDFloatLayout()

        # Top bar
        top_bar = MDBoxLayout(
            size_hint=(1, None),
            height=dp(56),
            pos_hint={"top": 1},
            padding=[dp(8), dp(4)],
        )
        back_btn = MDButton(
            MDButtonText(text="Voltar"),
            style="text",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
            on_release=self._on_back,
        )
        top_bar.add_widget(back_btn)
        top_bar.add_widget(MDLabel(
            text="Conectar WhatsApp",
            font_style="Title",
            role="medium",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_x=1.5,
        ))
        # Spacer for balance
        spacer = MDBoxLayout(size_hint_x=0.5)
        top_bar.add_widget(spacer)
        layout.add_widget(top_bar)

        # Main content card
        card = MDCard(
            orientation="vertical",
            size_hint=(0.88, 0.72),
            pos_hint={"center_x": 0.5, "center_y": 0.46},
            radius=[dp(28)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(24), dp(20)],
            spacing=dp(12),
            elevation=6,
        )

        # Title
        card.add_widget(MDLabel(
            text="Escaneie o QR Code",
            font_style="Headline",
            role="small",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        ))

        # QR Code area
        self.qr_container = MDCard(
            size_hint=(None, None),
            size=(dp(220), dp(220)),
            pos_hint={"center_x": 0.5},
            radius=[dp(16)],
            md_bg_color=(1, 1, 1, 1),
            elevation=4,
        )

        # Placeholder for QR code
        self.qr_placeholder = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
        )
        self.qr_placeholder.add_widget(MDLabel(
            text="📱",
            font_size=sp(48),
            halign="center",
        ))
        self.qr_loading = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            pos_hint={"center_x": 0.5},
            indicator_color=(0.424, 0.388, 1.0, 1),
        )
        self.qr_placeholder.add_widget(self.qr_loading)
        self.qr_container.add_widget(self.qr_placeholder)
        card.add_widget(self.qr_container)

        # Status label
        self.status_label = MDLabel(
            text="Gerando QR Code...",
            font_style="Body",
            role="medium",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        )
        card.add_widget(self.status_label)

        # Timer bar
        self.timer_bar = MDLinearProgressIndicator(
            size_hint_x=0.8,
            pos_hint={"center_x": 0.5},
            value=100,
            indicator_color=(0.424, 0.388, 1.0, 1),
            color=(0.2, 0.2, 0.3, 1),
        )
        card.add_widget(self.timer_bar)

        layout.add_widget(card)

        # Instructions card
        instructions_card = MDCard(
            orientation="vertical",
            size_hint=(0.88, None),
            height=dp(120),
            pos_hint={"center_x": 0.5, "y": 0.04},
            radius=[dp(16)],
            md_bg_color=(0.424, 0.388, 1.0, 0.1),
            padding=[dp(16), dp(12)],
            spacing=dp(4),
        )

        instructions_card.add_widget(MDLabel(
            text="Como conectar:",
            font_style="Title",
            role="small",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
        ))
        instructions_card.add_widget(MDLabel(
            text="1. Abra o WhatsApp no celular\n"
                 "2. Toque em ⋮ > Dispositivos conectados\n"
                 "3. Conectar um dispositivo > Escaneie",
            font_style="Label",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        ))

        layout.add_widget(instructions_card)
        self.add_widget(layout)

    def on_enter(self):
        """Start QR code generation when entering."""
        self._start_qr_refresh()

    def on_leave(self):
        """Stop refresh timer when leaving."""
        if self._refresh_event:
            self._refresh_event.cancel()
            self._refresh_event = None

    def _start_qr_refresh(self):
        """Start the QR code refresh cycle."""
        self._fetch_qr_code()
        # Refresh every 30 seconds
        self._refresh_event = Clock.schedule_interval(lambda dt: self._fetch_qr_code(), 30)

    def _fetch_qr_code(self):
        """Fetch QR code from API."""
        from apps.client.main import get_stored_token, get_stored_bot_id, api_request_async
        token = get_stored_token()
        bot_id = get_stored_bot_id()

        if not token:
            self.status_label.text = "Erro: nao autenticada"
            return

        self.status_label.text = "Gerando QR Code..."
        self.qr_loading.start()

        if bot_id:
            api_request_async("GET", f"/whatsapp/{bot_id}/qr", token=token, callback=self._on_qr_result)
        else:
            # Create bot first, then get QR
            self.status_label.text = "Criando bot..."

    def _on_qr_result(self, result):
        """Handle QR code response."""
        self.qr_loading.stop()

        if result["success"]:
            data = result["data"]
            qr_image = data.get("qr_image", "")
            status = data.get("status", "waiting")

            if status == "connected":
                self.status_label.text = "WhatsApp conectado! 🎉"
                self.status_label.text_color = (0.298, 0.686, 0.314, 1)
                self.timer_bar.value = 100
                self.timer_bar.indicator_color = (0.298, 0.686, 0.314, 1)
                if self._refresh_event:
                    self._refresh_event.cancel()
                # Auto-navigate to dashboard after 2 seconds
                Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'dashboard'), 2)
            else:
                self.status_label.text = "Escaneie o QR Code com seu celular"
                self.status_label.text_color = (0.7, 0.7, 0.75, 1)
                self.timer_bar.value = 100
                # Animate timer countdown
                self._animate_timer()
        else:
            error = result.get("error", "Erro ao gerar QR Code")
            self.status_label.text = f"Erro: {error}"
            self.status_label.text_color = (0.957, 0.263, 0.212, 1)

    def _animate_timer(self):
        """Animate the timer bar counting down."""
        self.timer_bar.value = 100
        anim = Animation(timer_bar_value=0, duration=28)
        # We'll just use a simple clock-based approach
        self._timer_value = 100
        Clock.schedule_interval(self._update_timer, 0.3)

    def _update_timer(self, dt):
        self._timer_value -= 1
        self.timer_bar.value = max(0, self._timer_value)
        if self._timer_value <= 0:
            return False
        return True

    def _on_back(self, instance):
        self.manager.current = "dashboard"
