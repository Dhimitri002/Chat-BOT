"""
WhatsApp Screen — Tela de conexao WhatsApp com QR Code.
========================================================
Gerencia a conexao WhatsApp do usuario:
- Geracao e exibicao de QR Code
- Status de conexao em tempo real via WebSocket
- Historico de conexao
- Desconexao
"""
import base64
import threading
from io import BytesIO

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.fitimage import FitImage


class WhatsAppScreen(MDScreen):
    """Tela de conexao WhatsApp com suporte a WebSocket em tempo real."""

    connection_status = StringProperty("disconnected")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "whatsapp"
        self._ws_handler_registered = False
        self._bot_id = None
        self.build()

    def build(self):
        from app_cliente.main import ThemeColors

        root = MDBoxLayout(
            orientation="vertical",
            md_bg_color=get_color_from_hex(ThemeColors.PRIMARY),
        )
        self.add_widget(root)

        # ---- Top Bar ----
        top_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=dp(12),
            spacing=dp(8),
            md_bg_color=get_color_from_hex(ThemeColors.SECONDARY),
        )

        back_btn = MDFlatButton(
            text="<-",
            font_size="24sp",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_x=None,
            width=dp(48),
        )
        back_btn.bind(on_release=self._go_back)
        top_bar.add_widget(back_btn)

        top_bar.add_widget(MDLabel(
            text="Conectar WhatsApp",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            bold=True,
        ))
        root.add_widget(top_bar)

        # ---- Content ----
        scroll = MDScrollView()
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=dp(20),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))
        scroll.add_widget(content)
        root.add_widget(scroll)

        # ---- Status Card ----
        self.status_card = MDCard(
            orientation="horizontal",
            spacing=dp(12),
            padding=dp(16),
            radius=[16],
            elevation=3,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
            height=dp(70),
        )

        self.status_icon = MDLabel(
            text="🔴",
            font_style="H5",
            size_hint_x=None,
            width=dp(40),
            halign="center",
        )

        status_text_box = MDBoxLayout(orientation="vertical")
        self.status_title = MDLabel(
            text="Desconectado",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        )
        self.status_desc = MDLabel(
            text="Conecte seu WhatsApp para comecar",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
            size_hint_y=None,
            height=dp(18),
        )
        status_text_box.add_widget(self.status_title)
        status_text_box.add_widget(self.status_desc)

        self.status_card.add_widget(self.status_icon)
        self.status_card.add_widget(status_text_box)
        content.add_widget(self.status_card)

        # ---- QR Code Card ----
        qr_card = MDCard(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(20),
            radius=[16],
            elevation=3,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
            height=dp(340),
        )

        qr_card.add_widget(MDLabel(
            text="Escaneie o QR Code",
            font_style="H6",
            halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(30),
            bold=True,
        ))

        # QR Widget area
        self.qr_widget = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(220),
            padding=dp(10),
        )
        self.qr_placeholder = MDLabel(
            text="Aguardando QR Code...",
            font_style="H6",
            halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
        )
        self.qr_widget.add_widget(self.qr_placeholder)
        qr_card.add_widget(self.qr_widget)

        # QR expiry countdown
        self.qr_expiry_label = MDLabel(
            text="",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
            size_hint_y=None,
            height=dp(20),
        )
        qr_card.add_widget(self.qr_expiry_label)

        self.loading_bar = MDProgressBar(
            type="indeterminate",
            opacity=0,
            size_hint_y=None,
            height=dp(4),
        )
        qr_card.add_widget(self.loading_bar)

        content.add_widget(qr_card)

        # ---- Steps Guide ----
        steps_card = MDCard(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(16),
            radius=[16],
            elevation=2,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
        )
        steps_card.bind(minimum_height=steps_card.setter("height"))

        steps_card.add_widget(MDLabel(
            text="Como conectar:",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        ))

        steps = [
            ("1", "Abra o WhatsApp no seu celular"),
            ("2", "Toque em Configuracoes > Dispositivos conectados"),
            ("3", "Toque em 'Conectar um dispositivo'"),
            ("4", "Escaneie o QR Code acima"),
        ]

        for num, desc in steps:
            step_row = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(8),
                size_hint_y=None,
                height=dp(28),
            )
            step_row.add_widget(MDLabel(
                text=f"  {num}  ",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
                size_hint_x=None,
                width=dp(32),
                bold=True,
            ))
            step_row.add_widget(MDLabel(
                text=desc,
                font_style="Body2",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
            ))
            steps_card.add_widget(step_row)

        content.add_widget(steps_card)

        # ---- Action Buttons ----
        btn_box = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(48),
        )

        self.connect_btn = MDRaisedButton(
            text="Gerar QR Code",
            md_bg_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_x=0.5,
            radius=[12],
        )
        self.connect_btn.bind(on_release=self._start_connection)
        btn_box.add_widget(self.connect_btn)

        self.disconnect_btn = MDRaisedButton(
            text="Desconectar",
            md_bg_color=get_color_from_hex(ThemeColors.ERROR),
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_x=0.5,
            radius=[12],
            opacity=0,
        )
        self.disconnect_btn.bind(on_release=self._disconnect)
        btn_box.add_widget(self.disconnect_btn)

        self.refresh_qr_btn = MDRaisedButton(
            text="Atualizar QR",
            md_bg_color=get_color_from_hex(ThemeColors.SECONDARY),
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_x=0.5,
            radius=[12],
            opacity=0,
        )
        self.refresh_qr_btn.bind(on_release=self._refresh_qr)
        btn_box.add_widget(self.refresh_qr_btn)

        content.add_widget(btn_box)

        # ---- Connection History ----
        history_card = MDCard(
            orientation="vertical",
            spacing=dp(4),
            padding=dp(16),
            radius=[16],
            elevation=2,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
            height=dp(100),
        )

        history_card.add_widget(MDLabel(
            text="Historico de Conexao",
            font_style="Subtitle1",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(24),
            bold=True,
        ))
        self.history_label = MDLabel(
            text="Nenhuma conexao anterior",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
        )
        history_card.add_widget(self.history_label)
        content.add_widget(history_card)

        content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(20)))

    # ── WebSocket Integration ─────────────────────────────────────

    def _register_ws_handlers(self):
        """Register WebSocket event handlers for real-time updates."""
        if self._ws_handler_registered:
            return

        from app_cliente.services.websocket_client import ws_client

        ws_client.on("connection_status", self._on_ws_connection_status)
        ws_client.on("qr_code", self._on_ws_qr_code)
        ws_client.on("message", self._on_ws_message)
        self._ws_handler_registered = True

    def _unregister_ws_handlers(self):
        """Unregister WebSocket event handlers."""
        if not self._ws_handler_registered:
            return

        from app_cliente.services.websocket_client import ws_client

        ws_client.off("connection_status", self._on_ws_connection_status)
        ws_client.off("qr_code", self._on_ws_qr_code)
        ws_client.off("message", self._on_ws_message)
        self._ws_handler_registered = False

    def _on_ws_connection_status(self, data):
        """Handle connection status update from WebSocket."""
        state = data.get("state", "disconnected")
        phone = data.get("phone_number", "")
        push_name = data.get("push_name", "")
        error = data.get("error_message", "")

        def _update(dt):
            if state == "connected":
                self.status_title.text = "Conectado!"
                self.status_desc.text = f"{push_name} ({phone})" if push_name else phone
                self.status_icon.text = "🟢"
                self.connect_btn.opacity = 0
                self.disconnect_btn.opacity = 1
                self.refresh_qr_btn.opacity = 0
                self.loading_bar.opacity = 0
                self.loading_bar.stop()
                self.history_label.text = f"Conectado as {Clock.get_time():.0f}"
            elif state == "qr_waiting":
                self.status_title.text = "Aguardando escaneamento..."
                self.status_desc.text = "Escaneie o QR Code com seu WhatsApp"
                self.status_icon.text = "🟡"
            elif state == "connecting":
                self.status_title.text = "Conectando..."
                self.status_desc.text = "Aguarde..."
                self.status_icon.text = "🟡"
            elif state == "reconnecting":
                self.status_title.text = "Reconectando..."
                self.status_desc.text = f"Tentativa {data.get('retry_count', 0)}"
                self.status_icon.text = "🟡"
            elif state == "logged_out":
                self.status_title.text = "Desconectado (logout)"
                self.status_desc.text = "Escaneie o QR Code novamente"
                self.status_icon.text = "🔴"
                self.connect_btn.opacity = 1
                self.connect_btn.disabled = False
                self.connect_btn.text = "Gerar QR Code"
                self.disconnect_btn.opacity = 0
                self.refresh_qr_btn.opacity = 0
            elif state == "error":
                self.status_title.text = "Erro de conexao"
                self.status_desc.text = error or "Tente novamente"
                self.status_icon.text = "🔴"
                self.connect_btn.disabled = False
                self.connect_btn.text = "Tentar novamente"
                self.loading_bar.opacity = 0
                self.loading_bar.stop()
            else:  # disconnected
                self.status_title.text = "Desconectado"
                self.status_desc.text = "Conecte seu WhatsApp para comecar"
                self.status_icon.text = "🔴"
                self.connect_btn.opacity = 1
                self.connect_btn.disabled = False
                self.connect_btn.text = "Gerar QR Code"
                self.disconnect_btn.opacity = 0
                self.refresh_qr_btn.opacity = 0

        Clock.schedule_once(_update, 0)

    def _on_ws_qr_code(self, data):
        """Handle QR code update from WebSocket."""
        qr_code = data.get("qr_code", "")
        expires_at = data.get("expires_at", "")

        def _update(dt):
            self._display_qr_code(qr_code)
            self.status_title.text = "QR Code gerado!"
            self.status_desc.text = "Escaneie com seu WhatsApp"
            self.status_icon.text = "🟢"
            self.connect_btn.opacity = 0
            self.disconnect_btn.opacity = 1
            self.refresh_qr_btn.opacity = 1
            self.loading_bar.opacity = 0
            self.loading_bar.stop()
            self.history_label.text = f"QR gerado - expira: {expires_at[:19] if expires_at else '60s'}"

        Clock.schedule_once(_update, 0)

    def _on_ws_message(self, data):
        """Handle incoming/outgoing message from WebSocket."""
        direction = data.get("direction", "")
        if direction == "in":
            self.status_desc.text = f"Nova mensagem de {data.get('from', 'desconhecido')}"
        elif direction == "out":
            self.status_desc.text = f"Mensagem enviada para {data.get('to', '')}"

    def _display_qr_code(self, qr_base64: str):
        """Display a QR code image from base64 data."""
        # Clear existing QR widget
        self.qr_widget.clear_widgets()

        if not qr_base64:
            self.qr_widget.add_widget(MDLabel(
                text="QR Code indisponivel",
                font_style="H6",
                halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex("#757575"),
            ))
            return

        try:
            # Remove data URL prefix if present
            if qr_base64.startswith("data:image"):
                qr_base64 = qr_base64.split(",", 1)[1]

            img_data = base64.b64decode(qr_base64)
            buf = BytesIO(img_data)
            buf.seek(0)

            core_img = CoreImage(buf, ext="png")
            img = FitImage(
                texture=core_img.texture,
                size_hint=(None, None),
                size=(dp(200), dp(200)),
                pos_hint={"center_x": 0.5},
            )
            self.qr_widget.add_widget(img)
        except Exception as e:
            print(f"[WhatsAppScreen] Error displaying QR: {e}")
            self.qr_widget.add_widget(MDLabel(
                text="Erro ao exibir QR Code",
                font_style="H6",
                halign="center",
                theme_text_color="Custom",
                text_color=get_color_from_hex("#ff5252"),
            ))

    # ── Connection Actions ────────────────────────────────────────

    def _start_connection(self, *args):
        """Inicia conexao WhatsApp e obtem QR code."""
        self.connect_btn.disabled = True
        self.connect_btn.text = "Conectando..."
        self.loading_bar.opacity = 1
        self.loading_bar.start()
        self.status_title.text = "Gerando QR Code..."
        self.status_desc.text = "Aguarde..."

        def _do():
            try:
                from app_cliente.services.api_client import api
                result = api.connect_whatsapp()
                qr_data = result.get("qr_code", "")
                state = result.get("state", "")
                session_id = result.get("session_id", "")

                if qr_data:
                    Clock.schedule_once(lambda dt: self._on_qr_ready(qr_data), 0)
                elif state == "connected":
                    Clock.schedule_once(lambda dt: self._on_connected(), 0)
                else:
                    Clock.schedule_once(
                        lambda dt: self._on_qr_error("Resposta inesperada do servidor"), 0
                    )
            except Exception as e:
                Clock.schedule_once(lambda dt: self._on_qr_error(str(e)), 0)

        threading.Thread(target=_do, daemon=True).start()

    def _on_qr_ready(self, qr_data):
        """QR code recebido."""
        self.loading_bar.opacity = 0
        self.loading_bar.stop()
        self.connect_btn.opacity = 0
        self.disconnect_btn.opacity = 1
        self.refresh_qr_btn.opacity = 1

        # Update status
        self.status_title.text = "QR Code gerado!"
        self.status_desc.text = "Escaneie com seu WhatsApp"
        self.status_icon.text = "🟢"

        # Display the QR code image
        self._display_qr_code(qr_data)

        self.status_card.md_bg_color = get_color_from_hex("#1a3a2e")
        self.history_label.text = f"QR gerado em {Clock.get_time():.0f}"

    def _on_connected(self):
        """Conectado com sucesso (sem QR)."""
        self.loading_bar.opacity = 0
        self.loading_bar.stop()
        self.connect_btn.opacity = 0
        self.disconnect_btn.opacity = 1
        self.refresh_qr_btn.opacity = 0
        self.status_title.text = "Conectado!"
        self.status_desc.text = "Seu WhatsApp esta funcionando"
        self.status_icon.text = "🟢"

    def _on_qr_error(self, error_msg):
        """Erro ao obter QR code."""
        self.loading_bar.opacity = 0
        self.loading_bar.stop()
        self.connect_btn.disabled = False
        self.connect_btn.text = "Gerar QR Code"
        self.status_title.text = "Erro ao gerar QR"
        self.status_desc.text = error_msg
        self.status_icon.text = "🔴"

    def _refresh_qr(self, *args):
        """Request a fresh QR code."""
        self.loading_bar.opacity = 1
        self.loading_bar.start()
        self.status_title.text = "Atualizando QR..."
        self.status_desc.text = "Aguarde..."

        def _do():
            try:
                from app_cliente.services.api_client import api
                result = api.refresh_whatsapp_qr()
                qr_data = result.get("qr_code", "")
                Clock.schedule_once(lambda dt: self._on_qr_ready(qr_data), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._on_qr_error(str(e)), 0)

        threading.Thread(target=_do, daemon=True).start()

    def _disconnect(self, *args):
        """Desconecta o WhatsApp."""
        self.status_title.text = "Desconectando..."
        self.status_desc.text = "Aguarde..."

        def _do():
            try:
                from app_cliente.services.api_client import api
                api.disconnect_whatsapp()
                Clock.schedule_once(lambda dt: self._on_disconnected(), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._on_qr_error(str(e)), 0)

        threading.Thread(target=_do, daemon=True).start()

    def _on_disconnected(self):
        """Desconectado."""
        self.status_title.text = "Desconectado"
        self.status_desc.text = "Conecte seu WhatsApp para comecar"
        self.status_icon.text = "🔴"
        self.connect_btn.opacity = 1
        self.connect_btn.disabled = False
        self.connect_btn.text = "Gerar QR Code"
        self.disconnect_btn.opacity = 0
        self.refresh_qr_btn.opacity = 0
        self.qr_widget.clear_widgets()
        self.qr_placeholder = MDLabel(
            text="Aguardando QR Code...",
            font_style="H6",
            halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex("#757575"),
        )
        self.qr_widget.add_widget(self.qr_placeholder)
        self.status_card.md_bg_color = get_color_from_hex("#1a1a2e")

    def _go_back(self, *args):
        self._unregister_ws_handlers()
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_enter(self):
        """Ao entrar, verifica status e registra handlers WebSocket."""
        self._register_ws_handlers()
        self._check_status()

    def on_leave(self):
        """Ao sair, desregistra handlers WebSocket."""
        self._unregister_ws_handlers()

    def _check_status(self):
        """Verifica status da conexao."""
        def _do():
            try:
                from app_cliente.services.api_client import api
                result = api.get_whatsapp_status()
                status = result.get("status", result.get("state", "disconnected"))
                phone = result.get("phone_number", "")
                push_name = result.get("push_name", "")
                Clock.schedule_once(
                    lambda dt: self._update_status(status, phone, push_name), 0
                )
            except Exception:
                pass

        threading.Thread(target=_do, daemon=True).start()

    def _update_status(self, status, phone="", push_name=""):
        """Atualiza UI com novo status."""
        if status == "connected":
            self.status_title.text = "Conectado!"
            self.status_desc.text = f"{push_name} ({phone})" if push_name else (phone or "WhatsApp conectado")
            self.status_icon.text = "🟢"
            self.connect_btn.opacity = 0
            self.disconnect_btn.opacity = 1
            self.refresh_qr_btn.opacity = 0
        elif status in ("connecting", "reconnecting"):
            self.status_title.text = "Conectando..."
            self.status_desc.text = "Aguardando escaneamento do QR"
            self.status_icon.text = "🟡"
        elif status == "qr_waiting":
            self.status_title.text = "Aguardando escaneamento..."
            self.status_desc.text = "Escaneie o QR Code com seu WhatsApp"
            self.status_icon.text = "🟡"
        elif status == "logged_out":
            self.status_title.text = "Desconectado (logout)"
            self.status_desc.text = "Escaneie o QR Code novamente"
            self.status_icon.text = "🔴"
        else:
            self.status_title.text = "Desconectado"
            self.status_desc.text = "Conecte seu WhatsApp para comecar"
            self.status_icon.text = "🔴"
