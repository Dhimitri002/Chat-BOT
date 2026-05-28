# ═══════════════════════════════════════════════════════════════
# Flora Platform — Tela de WhatsApp
# ═══════════════════════════════════════════════════════════════

from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.scrollview import ScrollView

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.textfield import MDTextField
from kivymd.uix.chip import MDChip
from kivymd.uix.dialog import MDDialog
from kivymd.toast import toast

from apps.shared.api_client import api


class WhatsAppScreen(Screen):
    """Tela de gerenciamento de conexões WhatsApp."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "whatsapp"
        self._dialog = None
        self._loading = False
        self._bots = []
        self._qr_data = {}
        self._build()
        Clock.schedule_once(lambda dt: self._load_bots(), 0.5)

    def _build(self):
        """Constrói a tela de WhatsApp."""
        self.md_bg_color = (0.059, 0.063, 0.137, 1)

        main_layout = MDBoxLayout(orientation="vertical")

        # ── Toolbar ─────────────────────────────────────────────
        toolbar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(16), dp(8)],
            md_bg_color=(0.11, 0.165, 0.298, 1),
        )

        back_btn = MDIconButton(
            icon="arrow-left",
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            on_release=lambda x: self._go_back(),
        )

        title = MDLabel(
            text="WhatsApp",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6",
            bold=True,
        )

        spacer = MDBoxLayout(size_hint_x=1)
        refresh_btn = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color=(0.145, 0.827, 0.4, 1),
            on_release=lambda x: self._load_bots(),
        )

        toolbar.add_widget(back_btn)
        toolbar.add_widget(title)
        toolbar.add_widget(spacer)
        toolbar.add_widget(refresh_btn)
        main_layout.add_widget(toolbar)

        # ── Info Banner ─────────────────────────────────────────
        info_banner = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            padding=[dp(16), dp(4)],
            md_bg_color=(0.145, 0.827, 0.4, 0.1),
        )

        info_banner.add_widget(MDIconButton(
            icon="information",
            theme_icon_color="Custom",
            icon_color=(0.145, 0.827, 0.4, 1),
            icon_size=dp(20),
            size_hint=(None, None),
            size=(dp(32), dp(32)),
        ))
        info_banner.add_widget(MDLabel(
            text="Conecte seus bots ao WhatsApp escaneando o QR Code",
            theme_text_color="Custom",
            text_color=(0.145, 0.827, 0.4, 1),
            font_style="Caption",
        ))
        main_layout.add_widget(info_banner)

        # ── Lista de Bots com Status WhatsApp ───────────────────
        scroll = ScrollView()
        self.bots_list = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(8)],
            spacing=dp(12),
            size_hint_y=None,
        )
        self.bots_list.bind(minimum_height=self.bots_list.setter("height"))

        self._loading_box = MDBoxLayout(size_hint_y=None, height=dp(200))
        self._spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            active=True,
        )
        self._loading_box.add_widget(self._spinner)
        self.bots_list.add_widget(self._loading_box)

        scroll.add_widget(self.bots_list)
        main_layout.add_widget(scroll)

        self.add_widget(main_layout)

    def _load_bots(self):
        if self._loading:
            return
        self._loading = True
        self._spinner.active = True
        self._loading_box.height = dp(200)
        self._loading_box.opacity = 1

        def _on_result(result):
            Clock.schedule_once(lambda dt: self._handle_bots(result), 0)

        api.get_async("/admin/bots", _on_result)

    def _handle_bots(self, result):
        self._loading = False
        self._loading_box.height = dp(0)
        self._loading_box.opacity = 0
        self._spinner.active = False

        if result.get("error"):
            toast("Erro ao carregar bots.")
            return

        self._bots = result.get("bots", [])
        self._render_bots()

    def _render_bots(self):
        self.bots_list.clear_widgets()

        if not self._bots:
            empty = MDBoxLayout(size_hint_y=None, height=dp(120))
            empty.add_widget(MDLabel(
                text="Nenhum bot encontrado. Crie um bot primeiro.",
                theme_text_color="Custom",
                text_color=(0.376, 0.49, 0.545, 1),
                font_style="Body1",
                halign="center",
            ))
            self.bots_list.add_widget(empty)
            return

        for bot in self._bots:
            card = self._create_wa_card(bot)
            self.bots_list.add_widget(card)

    def _create_wa_card(self, bot):
        bot_id = bot.get("id", "")
        bot_name = bot.get("name", "Sem nome")
        is_connected = bot.get("is_connected", False)
        is_active = bot.get("is_active", False)

        if is_connected:
            status_color = (0.145, 0.827, 0.4, 1)
            status_text = "Conectado"
            status_icon = "check-circle"
        elif is_active:
            status_color = (0.957, 0.612, 0.0, 1)
            status_text = "Desconectado"
            status_icon = "alert-circle"
        else:
            status_color = (0.957, 0.263, 0.212, 1)
            status_text = "Inativo"
            status_icon = "close-circle"

        card = MDCard(
            orientation="vertical",
            radius=[dp(16)],
            elevation=2,
            padding=dp(16),
            spacing=dp(12),
            size_hint_y=None,
            height=dp(280),
            md_bg_color=(0.11, 0.165, 0.298, 1),
        )

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
        )

        header.add_widget(MDLabel(
            text=f"🤖 {bot_name}",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6",
            bold=True,
            size_hint_x=0.7,
        ))
        header.add_widget(MDChip(
            text=f"  {status_text}  ",
            icon=status_icon,
            md_bg_color=(*status_color[:3], 0.15),
            text_color=status_color,
            size_hint_x=None,
            width=dp(110),
            height=dp(28),
            font_size=dp(11),
        ))
        card.add_widget(header)

        # QR Code Area
        qr_area = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(140),
            padding=dp(8),
        )

        if is_connected:
            qr_area.add_widget(MDLabel(
                text="✅ WhatsApp conectado e funcionando!",
                theme_text_color="Custom",
                text_color=(0.145, 0.827, 0.4, 1),
                font_style="Body1",
                halign="center",
            ))
        else:
            qr_area.add_widget(MDLabel(
                text="📱 Escaneie o QR Code com o WhatsApp",
                theme_text_color="Custom",
                text_color=(0.69, 0.745, 0.773, 1),
                font_style="Body2",
                halign="center",
            ))

            # QR Code placeholder
            qr_placeholder = MDCard(
                size_hint=(None, None),
                size=(dp(100), dp(100)),
                pos_hint={"center_x": 0.5},
                radius=[dp(8)],
                md_bg_color=(0.055, 0.106, 0.243, 1),
            )
            qr_placeholder.add_widget(MDLabel(
                text="QR",
                theme_text_color="Custom",
                text_color=(0.376, 0.49, 0.545, 1),
                font_style="H5",
                halign="center",
                valign="middle",
            ))
            qr_area.add_widget(qr_placeholder)

        card.add_widget(qr_area)

        # Ações
        actions = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(8),
        )

        if is_connected:
            disconnect_btn = MDRaisedButton(
                text="Desconectar",
                md_bg_color=(0.957, 0.263, 0.212, 1),
                text_color=(1, 1, 1, 1),
                radius=[dp(12)],
                size_hint_x=0.5,
                on_release=lambda x, b=bot: self._disconnect(b),
            )
            actions.add_widget(disconnect_btn)

            test_btn = MDFlatButton(
                text="Enviar Teste",
                theme_text_color="Custom",
                text_color=(0.129, 0.588, 0.953, 1),
                font_style="Button",
                size_hint_x=0.5,
                on_release=lambda x, b=bot: self._send_test(b),
            )
            actions.add_widget(test_btn)
        else:
            connect_btn = MDRaisedButton(
                text="Conectar WhatsApp",
                md_bg_color=(0.145, 0.827, 0.4, 1),
                text_color=(1, 1, 1, 1),
                radius=[dp(12)],
                size_hint_x=0.6,
                on_release=lambda x, b=bot: self._connect(b),
            )
            actions.add_widget(connect_btn)

            refresh_qr_btn = MDFlatButton(
                text="Atualizar QR",
                theme_icon_color="Custom",
                theme_text_color="Custom",
                text_color=(0.424, 0.388, 1.0, 1),
                font_style="Button",
                size_hint_x=0.4,
                on_release=lambda x, b=bot: self._refresh_qr(b),
            )
            actions.add_widget(refresh_qr_btn)

        card.add_widget(actions)
        return card

    def _connect(self, bot):
        """Inicia conexão WhatsApp para o bot."""
        bot_id = bot.get("id")
        toast("Iniciando conexão WhatsApp...")

        def _on_result(result):
            Clock.schedule_once(lambda dt: self._handle_connect(result, bot_id), 0)

        api.post_async(f"/whatsapp/connect/{bot_id}", _on_result)

    def _handle_connect(self, result, bot_id):
        if result.get("error"):
            toast("Erro ao conectar. Tente novamente.")
        else:
            toast("QR Code gerado! Escaneie com o WhatsApp.")
            self._load_bots()

    def _disconnect(self, bot):
        """Desconecta o bot do WhatsApp."""
        bot_id = bot.get("id")

        if self._dialog:
            self._dialog.dismiss()

        self._dialog = MDDialog(
            title="Desconectar WhatsApp",
            text="Tem certeza que deseja desconectar este bot?",
            buttons=[
                MDFlatButton(
                    text="Cancelar",
                    theme_text_color="Custom",
                    text_color=(0.69, 0.745, 0.773, 1),
                    on_release=lambda x: self._dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="Desconectar",
                    md_bg_color=(0.957, 0.263, 0.212, 1),
                    text_color=(1, 1, 1, 1),
                    on_release=lambda x: self._do_disconnect(bot_id),
                ),
            ],
        )
        self._dialog.open()

    def _do_disconnect(self, bot_id):
        self._dialog.dismiss()

        def _on_result(result):
            Clock.schedule_once(lambda dt: self._handle_disconnect(result), 0)

        api.post_async(f"/whatsapp/disconnect/{bot_id}", _on_result)

    def _handle_disconnect(self, result):
        if result.get("error"):
            toast("Erro ao desconectar.")
        else:
            toast("WhatsApp desconectado.")
            self._load_bots()

    def _refresh_qr(self, bot):
        """Atualiza o QR Code."""
        bot_id = bot.get("id")
        toast("Atualizando QR Code...")

        def _on_result(result):
            Clock.schedule_once(lambda dt: None, 0)

        api.post_async(f"/whatsapp/refresh-qr/{bot_id}", _on_result)

    def _send_test(self, bot):
        """Envia mensagem de teste."""
        bot_id = bot.get("id")
        toast("Enviando mensagem de teste...")

        def _on_result(result):
            Clock.schedule_once(lambda dt: self._handle_test(result), 0)

        api.post_async(f"/whatsapp/send/{bot_id}", _on_result, {
            "to": "",
            "text": "🌸 Mensagem de teste da Flora Platform!"
        })

    def _handle_test(self, result):
        if result.get("error"):
            toast("Erro ao enviar mensagem.")
        else:
            toast("Mensagem de teste enviada!")

    def _go_back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"

    def on_enter(self, *args):
        Clock.schedule_once(lambda dt: self._load_bots(), 0.3)
        return super().on_enter(*args)
