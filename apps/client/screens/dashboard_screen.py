# ═══════════════════════════════════════════════════════════════
# Flora Platform — Dashboard Screen
# ═══════════════════════════════════════════════════════════════

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.divider import MDDivider
from kivymd.uix.list import MDList, MDListItem, MDListItemHeadlineText, MDListItemSupportingText, MDListItemLeadingIcon


class DashboardScreen(MDScreen):
    """Main dashboard after login - overview of bot status and quick actions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        self.md_bg_color = (0.102, 0.102, 0.180, 1)

        layout = MDFloatLayout()

        # ── Top Header ──────────────────────────────────
        header = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(140),
            pos_hint={"top": 1},
            padding=[dp(20), dp(12), dp(20), dp(8)],
            spacing=dp(2),
        )

        # Greeting
        self.greeting_label = MDLabel(
            text="Ola! 🌸",
            font_style="Headline",
            role="small",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )
        header.add_widget(self.greeting_label)

        # Subtitle
        subtitle = MDLabel(
            text="Aqui esta o resumo do seu bot",
            font_style="Body",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        )
        header.add_widget(subtitle)

        layout.add_widget(header)

        # ── Scrollable Content ──────────────────────────
        scroll = MDScrollView(
            pos_hint={"top": 0.82},
            size_hint=(1, 0.78),
            do_scroll_x=False,
        )
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=[dp(16), dp(8), dp(16), dp(100)],
            size_hint_y=None,
            adaptive_height=True,
        )

        # ── Bot Status Card ─────────────────────────────
        status_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(130),
            radius=[dp(20)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(20), dp(16)],
            spacing=dp(8),
            elevation=4,
        )

        status_header = MDBoxLayout(
            size_hint=(1, None),
            height=dp(32),
            spacing=dp(8),
        )
        status_header.add_widget(MDLabel(
            text="Status do Bot",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_x=0.7,
        ))

        # Status indicator chip
        self.status_chip = MDChip(
            MDChipText(
                text="Desconectado",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
            ),
            md_bg_color=(0.957, 0.263, 0.212, 0.3),
        )
        status_header.add_widget(self.status_chip)
        status_card.add_widget(status_header)

        # Bot info
        self.bot_name_label = MDLabel(
            text="Bot nao configurado",
            font_style="Title",
            role="small",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
        )
        status_card.add_widget(self.bot_name_label)

        self.bot_phone_label = MDLabel(
            text="📱 Nenhum numero conectado",
            font_style="Label",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        )
        status_card.add_widget(self.bot_phone_label)

        content.add_widget(status_card)

        # ── Quick Stats ─────────────────────────────────
        stats_grid = MDGridLayout(
            cols=3,
            spacing=dp(10),
            size_hint=(1, None),
            height=dp(90),
        )

        stats_data = [
            ("0", "Msgs Hoje 💬"),
            ("0", "Total 📊"),
            ("0", "Usuarios 👥"),
        ]

        self.stat_labels = []
        for val, label in stats_data:
            stat_card = MDCard(
                orientation="vertical",
                radius=[dp(14)],
                md_bg_color=(0.13, 0.16, 0.28, 1),
                padding=[dp(8)],
                elevation=2,
            )
            val_label = MDLabel(
                text=val,
                font_style="Title",
                role="large",
                halign="center",
                theme_text_color="Custom",
                text_color=(0.424, 0.388, 1.0, 1),
            )
            self.stat_labels.append(val_label)
            stat_card.add_widget(val_label)
            stat_card.add_widget(MDLabel(
                text=label,
                font_style="Label",
                role="small",
                halign="center",
                theme_text_color="Custom",
                text_color=(0.7, 0.7, 0.75, 1),
            ))
            stats_grid.add_widget(stat_card)

        content.add_widget(stats_grid)

        # ── Quick Actions ───────────────────────────────
        content.add_widget(MDLabel(
            text="Acoes Rapidas",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(32),
        ))

        actions_grid = MDGridLayout(
            cols=2,
            spacing=dp(10),
            size_hint=(1, None),
            height=dp(200),
        )

        actions = [
            ("Conectar WhatsApp", "📱", "whatsapp_qr"),
            ("Ver Chat", "💬", "chat"),
            ("Configurar Bot", "⚙️", "bot_config"),
            ("Falar com Flora", "🌸", "flora_chat"),
        ]

        for label_text, emoji, screen in actions:
            action_card = MDCard(
                orientation="vertical",
                radius=[dp(16)],
                md_bg_color=(0.13, 0.16, 0.28, 1),
                padding=[dp(16)],
                elevation=2,
                on_release=lambda x, s=screen: self._navigate_to(s),
            )
            action_card.add_widget(MDLabel(
                text=emoji,
                font_size=sp(32),
                halign="center",
                size_hint_y=0.5,
            ))
            action_card.add_widget(MDLabel(
                text=label_text,
                font_style="Title",
                role="small",
                halign="center",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
            ))
            actions_grid.add_widget(action_card)

        content.add_widget(actions_grid)

        # ── Recent Messages ─────────────────────────────
        content.add_widget(MDLabel(
            text="Mensagens Recentes",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(32),
        ))

        self.recent_list = MDList(
            spacing=dp(4),
        )

        # Placeholder items
        for i in range(3):
            item = MDListItem(
                MDListItemLeadingIcon(
                    icon="message-text-outline",
                    theme_text_color="Custom",
                    text_color=(0.424, 0.388, 1.0, 1),
                ),
                MDListItemHeadlineText(
                    text="Nenhuma mensagem ainda",
                    theme_text_color="Custom",
                    text_color=(0.7, 0.7, 0.75, 1),
                ),
                MDListItemSupportingText(
                    text="Conecte o WhatsApp para comecar",
                    theme_text_color="Custom",
                    text_color=(0.5, 0.5, 0.55, 1),
                ),
                radius=[dp(12)],
                md_bg_color=(0.13, 0.16, 0.28, 0.5),
            )
            self.recent_list.add_widget(item)

        content.add_widget(self.recent_list)

        scroll.add_widget(content)
        layout.add_widget(scroll)

        # ── Bottom Navigation ───────────────────────────
        from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem

        bottom_nav = MDBottomNavigation(
            panel_color=(0.13, 0.16, 0.28, 1),
            text_color_active=(0.424, 0.388, 1.0, 1),
            text_color_inactive=(0.5, 0.5, 0.55, 1),
            selected_color_background=(0.424, 0.388, 1.0, 0.15),
            radius=[dp(20), dp(20), 0, 0],
            elevation=8,
        )

        nav_items = [
            ("home", "Inicio", "dashboard"),
            ("whatsapp", "WhatsApp", "whatsapp_qr"),
            ("chat", "Chat", "chat"),
            ("robot", "Bot", "bot_config"),
            ("account", "Perfil", "profile"),
        ]

        for icon_name, text, screen in nav_items:
            item = MDBottomNavigationItem(
                name=f"nav_{screen}",
                text=text,
                icon=icon_name,
                on_release=lambda x, s=screen: self._navigate_to(s),
            )
            bottom_nav.add_widget(item)

        layout.add_widget(bottom_nav)
        self.add_widget(layout)

    def on_enter(self):
        """Called when entering the dashboard."""
        self._load_user_data()
        self._refresh_data()

    def _load_user_data(self):
        """Load user data from storage."""
        from apps.client.main import get_stored_user, load_token_data
        user = get_stored_user()
        data = load_token_data()

        if user:
            name = user.get("name", "Usuaria")
            self.greeting_label.text = f"Ola, {name}! 🌸"

        if data:
            bot_name = data.get("bot_name", "Meu Bot Flora")
            self.bot_name_label.text = f"🤖 {bot_name}"

    def _refresh_data(self):
        """Refresh dashboard data from API."""
        from apps.client.main import get_stored_token, api_request_async, get_stored_bot_id
        token = get_stored_token()
        bot_id = get_stored_bot_id()

        if token and bot_id:
            api_request_async("GET", f"/bots/{bot_id}", token=token, callback=self._on_bot_data)

    def _on_bot_data(self, result):
        """Handle bot data response."""
        if result["success"] and result["data"]:
            bot = result["data"]
            status = bot.get("status", "disconnected")
            phone = bot.get("phone_number", "")

            if status == "connected":
                self.status_chip.children[0].text = "Conectado"
                self.status_chip.md_bg_color = (0.298, 0.686, 0.314, 0.3)
                self.bot_phone_label.text = f"📱 {phone}" if phone else "📱 Conectado"
            else:
                self.status_chip.children[0].text = "Desconectado"
                self.status_chip.md_bg_color = (0.957, 0.263, 0.212, 0.3)
                self.bot_phone_label.text = "📱 Nenhum numero conectado"

    def _navigate_to(self, screen: str):
        """Navigate to a different screen."""
        self.manager.current = screen
