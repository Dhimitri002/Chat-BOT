# ═══════════════════════════════════════════════════════════════
# Flora Platform — Bot Config Screen
# ═══════════════════════════════════════════════════════════════

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.divider import MDDivider


class BotConfigScreen(MDScreen):
    """Bot configuration form screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
            md_bg_color=(0.13, 0.16, 0.28, 1),
            elevation=4,
        )
        back_btn = MDIconButton(
            icon="arrow-left",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
            on_release=self._on_back,
        )
        top_bar.add_widget(back_btn)
        top_bar.add_widget(MDLabel(
            text="Configurar Bot ⚙️",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        ))
        layout.add_widget(top_bar)

        # Scrollable form
        scroll = MDScrollView(
            pos_hint={"top": 0.92},
            size_hint=(1, 0.92),
            do_scroll_x=False,
        )

        form = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=[dp(16), dp(8), dp(16), dp(100)],
            size_hint_y=None,
            adaptive_height=True,
        )

        # ── Bot Identity Section ───────────────────────
        form.add_widget(MDLabel(
            text="Identidade do Bot",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            size_hint_y=None,
            height=dp(32),
        ))

        # Bot name
        self.name_input = MDTextField(
            mode="outlined",
            hint_text="Nome do Bot",
            text="Meu Bot Flora",
            line_color_focus=(0.424, 0.388, 1.0, 1),
            line_color_normal=(0.3, 0.3, 0.4, 1),
            text_color_normal=(0.7, 0.7, 0.75, 1),
            text_color_focus=(1, 1, 1, 1),
            fill_color_normal=(0.13, 0.16, 0.28, 1),
        )
        form.add_widget(self.name_input)

        # Description
        self.desc_input = MDTextField(
            mode="outlined",
            hint_text="Descricao do Bot",
            text="",
            multiline=True,
            max_height=dp(100),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            line_color_normal=(0.3, 0.3, 0.4, 1),
            text_color_normal=(0.7, 0.7, 0.75, 1),
            text_color_focus=(1, 1, 1, 1),
            fill_color_normal=(0.13, 0.16, 0.28, 1),
        )
        form.add_widget(self.desc_input)

        form.add_widget(MDDivider())

        # ── Personality Section ────────────────────────
        form.add_widget(MDLabel(
            text="Personalidade",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            size_hint_y=None,
            height=dp(32),
        ))

        # Personality chips
        personalities = [
            ("amigavel", "😊 Amigavel"),
            ("profissional", "💼 Profissional"),
            ("divertido", "🎉 Divertido"),
            ("formal", "🎩 Formal"),
        ]

        pers_box = MDBoxLayout(
            spacing=dp(8),
            size_hint_y=None,
            height=dp(44),
            padding=[dp(4)],
        )

        self.personality_chips = {}
        for pers_id, pers_label in personalities:
            chip = MDChip(
                MDChipText(
                    text=pers_label,
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1) if pers_id == "amigavel" else (0.7, 0.7, 0.75, 1),
                ),
                type="filter",
                selected=(pers_id == "amigavel"),
                md_bg_color=(0.424, 0.388, 1.0, 0.3) if pers_id == "amigavel" else (0.2, 0.2, 0.3, 1),
                on_release=lambda x, pid=pers_id: self._select_personality(pid),
            )
            self.personality_chips[pers_id] = chip
            pers_box.add_widget(chip)

        form.add_widget(pers_box)
        self.selected_personality = "amigavel"

        form.add_widget(MDDivider())

        # ── Messages Section ───────────────────────────
        form.add_widget(MDLabel(
            text="Mensagens",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            size_hint_y=None,
            height=dp(32),
        ))

        # Welcome message
        self.welcome_input = MDTextField(
            mode="outlined",
            hint_text="Mensagem de Boas-vindas",
            text="Ola! 👋 Como posso te ajudar?",
            multiline=True,
            max_height=dp(80),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            line_color_normal=(0.3, 0.3, 0.4, 1),
            text_color_normal=(0.7, 0.7, 0.75, 1),
            text_color_focus=(1, 1, 1, 1),
            fill_color_normal=(0.13, 0.16, 0.28, 1),
        )
        form.add_widget(self.welcome_input)

        # Farewell message
        self.farewell_input = MDTextField(
            mode="outlined",
            hint_text="Mensagem de Despedida",
            text="Ate mais! 👋 Foi um prazer ajudar!",
            multiline=True,
            max_height=dp(80),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            line_color_normal=(0.3, 0.3, 0.4, 1),
            text_color_normal=(0.7, 0.7, 0.75, 1),
            text_color_focus=(1, 1, 1, 1),
            fill_color_normal=(0.13, 0.16, 0.28, 1),
        )
        form.add_widget(self.farewell_input)

        form.add_widget(MDDivider())

        # ── Preview Section ────────────────────────────
        form.add_widget(MDLabel(
            text="Pre-visualizacao",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            size_hint_y=None,
            height=dp(32),
        ))

        preview_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(80),
            radius=[dp(16)],
            md_bg_color=(0.2, 0.23, 0.35, 1),
            padding=[dp(16), dp(12)],
            spacing=dp(4),
        )
        preview_card.add_widget(MDLabel(
            text="🤖 Bot diz:",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        ))
        self.preview_label = MDLabel(
            text="Ola! 👋 Como posso te ajudar?",
            font_style="Body",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )
        preview_card.add_widget(self.preview_label)
        form.add_widget(preview_card)

        # ── Action Buttons ─────────────────────────────
        form.add_widget(MDBoxLayout(size_hint_y=None, height=dp(8)))

        save_btn = MDButton(
            MDButtonText(text="Salvar Configuracao"),
            style="filled",
            size_hint=(1, None),
            height=dp(52),
            md_bg_color=(0.424, 0.388, 1.0, 1),
            on_release=self._on_save,
        )
        form.add_widget(save_btn)

        reset_btn = MDButton(
            MDButtonText(text="Restaurar Padroes"),
            style="outlined",
            size_hint=(1, None),
            height=dp(48),
            line_color=(1.0, 0.420, 0.616, 1),
            text_color=(1.0, 0.420, 0.616, 1),
            on_release=self._on_reset,
        )
        form.add_widget(reset_btn)

        scroll.add_widget(form)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def _select_personality(self, pers_id: str):
        """Select a personality."""
        self.selected_personality = pers_id
        for pid, chip in self.personality_chips.items():
            if pid == pers_id:
                chip.selected = True
                chip.md_bg_color = (0.424, 0.388, 1.0, 0.3)
                chip.children[0].text_color = (1, 1, 1, 1)
            else:
                chip.selected = False
                chip.md_bg_color = (0.2, 0.2, 0.3, 1)
                chip.children[0].text_color = (0.7, 0.7, 0.75, 1)

    def on_enter(self):
        """Load current bot config when entering."""
        self._load_config()

    def _load_config(self):
        """Load bot configuration from API."""
        from apps.client.main import get_stored_token, get_stored_bot_id, api_request_async
        token = get_stored_token()
        bot_id = get_stored_bot_id()

        if token and bot_id:
            api_request_async("GET", f"/bots/{bot_id}", token=token, callback=self._on_config_loaded)

    def _on_config_loaded(self, result):
        """Handle loaded config."""
        if result["success"] and result["data"]:
            bot = result["data"]
            Clock.schedule_once(lambda dt: self._populate_fields(bot), 0)

    def _populate_fields(self, bot: dict):
        """Populate form fields with bot data."""
        self.name_input.text = bot.get("name", "")
        self.desc_input.text = bot.get("description", "")
        self.welcome_input.text = bot.get("welcome_message", "Ola! 👋 Como posso te ajudar?")
        self.farewell_input.text = bot.get("farewell_message", "Ate mais! 👋")
        personality = bot.get("personality", "amigavel")
        if personality in self.personality_chips:
            self._select_personality(personality)
        self.preview_label.text = self.welcome_input.text

    def _on_save(self, instance):
        """Save bot configuration."""
        from apps.client.main import get_stored_token, get_stored_bot_id, api_request_async
        token = get_stored_token()
        bot_id = get_stored_bot_id()

        data = {
            "name": self.name_input.text.strip() or "Meu Bot Flora",
            "description": self.desc_input.text.strip(),
            "personality": self.selected_personality,
            "welcome_message": self.welcome_input.text.strip() or "Ola! 👋",
            "farewell_message": self.farewell_input.text.strip() or "Ate mais! 👋",
        }

        if token and bot_id:
            api_request_async("PUT", f"/bots/{bot_id}", data=data, token=token, callback=self._on_saved)
        else:
            # Save locally
            from apps.client.main import save_token_data, load_token_data
            stored = load_token_data() or {}
            stored["bot_config"] = data
            save_token_data(stored)
            self._show_success()

    def _on_saved(self, result):
        """Handle save response."""
        if result["success"]:
            self._show_success()
        else:
            error = result.get("error", "Erro ao salvar")
            app = MDApp.get_running_app() if hasattr(MDApp, 'get_running_app') else None

    def _show_success(self):
        """Show success feedback."""
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            if app and hasattr(app, 'show_snackbar'):
                app.show_snackbar("Configuracao salva com sucesso!", (0.298, 0.686, 0.314, 1))
        except Exception:
            pass

    def _on_reset(self, instance):
        """Reset to default values."""
        self.name_input.text = "Meu Bot Flora"
        self.desc_input.text = ""
        self.welcome_input.text = "Ola! 👋 Como posso te ajudar?"
        self.farewell_input.text = "Ate mais! 👋 Foi um prazer ajudar!"
        self._select_personality("amigavel")
        self.preview_label.text = self.welcome_input.text

    def _on_back(self, instance):
        self.manager.current = "dashboard"
