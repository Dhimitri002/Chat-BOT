# ═══════════════════════════════════════════════════════════════
# Flora Platform — Onboarding Screen
# ═══════════════════════════════════════════════════════════════

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.progressindicator import MDLinearProgressIndicator
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.dropdownitem import MDDropDownItem
from kivymd.uix.menu import MDDropdownMenu


class OnboardingScreen(MDScreen):
    """Multi-step onboarding: bot setup, WhatsApp connection, completion."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_step = 0
        self.total_steps = 3
        self.bot_name = ""
        self.bot_personality = "amigavel"
        self._step_cache = {}
        self._build_ui()

    def _build_ui(self):
        self.md_bg_color = (0.102, 0.102, 0.180, 1)

        layout = MDFloatLayout()

        # Progress bar
        self.progress = MDLinearProgressIndicator(
            size_hint_x=0.88,
            pos_hint={"center_x": 0.5, "top": 0.97},
            value=33,
            indicator_color=(0.424, 0.388, 1.0, 1),
            color=(0.2, 0.2, 0.3, 1),
        )
        layout.add_widget(self.progress)

        # Step label
        self.step_label = MDLabel(
            text="Passo 1 de 3",
            font_style="Label",
            role="medium",
            halign="center",
            pos_hint={"center_x": 0.5, "top": 0.93},
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        )
        layout.add_widget(self.step_label)

        # Content card
        self.content_card = MDCard(
            orientation="vertical",
            size_hint=(0.88, 0.68),
            pos_hint={"center_x": 0.5, "center_y": 0.45},
            radius=[dp(28)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(28), dp(24)],
            spacing=dp(16),
            elevation=6,
        )
        layout.add_widget(self.content_card)

        # Navigation buttons
        nav_box = MDBoxLayout(
            size_hint=(0.88, None),
            height=dp(52),
            pos_hint={"center_x": 0.5, "y": 0.04},
            spacing=dp(12),
        )

        self.back_btn = MDButton(
            MDButtonText(text="Voltar"),
            style="outlined",
            size_hint_x=0.35,
            line_color=(0.424, 0.388, 1.0, 1),
            text_color=(0.424, 0.388, 1.0, 1),
            on_release=self._on_back,
            opacity=0,
            disabled=True,
        )
        nav_box.add_widget(self.back_btn)

        self.next_btn = MDButton(
            MDButtonText(text="Proximo"),
            style="filled",
            size_hint_x=0.65,
            md_bg_color=(0.424, 0.388, 1.0, 1),
            on_release=self._on_next,
        )
        nav_box.add_widget(self.next_btn)

        layout.add_widget(nav_box)
        self.add_widget(layout)

        self._show_step(0)

    def _clear_card(self):
        self.content_card.clear_widgets()

    def _show_step(self, step: int):
        """Show the given onboarding step."""
        self.current_step = step
        self.progress.value = int((step + 1) / self.total_steps * 100)
        self.step_label.text = f"Passo {step + 1} de {self.total_steps}"

        if step > 0:
            self.back_btn.opacity = 1
            self.back_btn.disabled = False
        else:
            self.back_btn.opacity = 0
            self.back_btn.disabled = True

        if step == self.total_steps - 1:
            self.next_btn.children[0].children[0].text = "Ir para Dashboard"
        else:
            self.next_btn.children[0].children[0].text = "Proximo"

        self._clear_card()

        if step == 0:
            self._build_step_1()
        elif step == 1:
            self._build_step_2()
        elif step == 2:
            self._build_step_3()

    def _build_step_1(self):
        """Step 1: Bot name and personality."""
        # Title
        title = MDLabel(
            text="Seu Bot 🤖",
            font_style="Headline",
            role="small",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )
        self.content_card.add_widget(title)

        # Subtitle
        subtitle = MDLabel(
            text="Escolha um nome e a personalidade do seu chatbot.",
            font_style="Body",
            role="medium",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        )
        self.content_card.add_widget(subtitle)

        # Spacer
        self.content_card.add_widget(MDBoxLayout(size_hint_y=None, height=dp(16)))

        # Bot name input
        self.bot_name_input = MDTextField(
            mode="outlined",
            hint_text="Nome do Bot",
            text=self.bot_name,
            line_color_focus=(0.424, 0.388, 1.0, 1),
            line_color_normal=(0.3, 0.3, 0.4, 1),
            text_color_normal=(0.7, 0.7, 0.75, 1),
            text_color_focus=(1, 1, 1, 1),
            fill_color_normal=(0.13, 0.16, 0.28, 1),
        )
        self.content_card.add_widget(self.bot_name_input)

        # Personality label
        pers_label = MDLabel(
            text="Personalidade:",
            font_style="Title",
            role="small",
            theme_text_color="Custom",
            text_color=(0.8, 0.8, 0.85, 1),
            size_hint_y=None,
            height=dp(32),
        )
        self.content_card.add_widget(pers_label)

        # Personality chips
        personalities = [
            ("amigavel", "😊 Amigavel"),
            ("profissional", "💼 Profissional"),
            ("divertido", "🎉 Divertido"),
            ("formal", "🎩 Formal"),
        ]

        chips_box = MDBoxLayout(
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
                    text_color=(1, 1, 1, 1) if self.bot_personality == pers_id else (0.7, 0.7, 0.75, 1),
                ),
                type="filter",
                selected=self.bot_personality == pers_id,
                md_bg_color=(0.424, 0.388, 1.0, 0.3) if self.bot_personality == pers_id else (0.2, 0.2, 0.3, 1),
                on_release=lambda x, pid=pers_id: self._select_personality(pid),
            )
            self.personality_chips[pers_id] = chip
            chips_box.add_widget(chip)

        self.content_card.add_widget(chips_box)

    def _select_personality(self, pers_id: str):
        """Select a personality for the bot."""
        self.bot_personality = pers_id
        for pid, chip in self.personality_chips.items():
            if pid == pers_id:
                chip.selected = True
                chip.md_bg_color = (0.424, 0.388, 1.0, 0.3)
                chip.children[0].text_color = (1, 1, 1, 1)
            else:
                chip.selected = False
                chip.md_bg_color = (0.2, 0.2, 0.3, 1)
                chip.children[0].text_color = (0.7, 0.7, 0.75, 1)

    def _build_step_2(self):
        """Step 2: WhatsApp connection explanation."""
        # Icon
        icon = MDLabel(
            text="📱",
            font_size=sp(64),
            halign="center",
            size_hint_y=None,
            height=dp(80),
        )
        self.content_card.add_widget(icon)

        # Title
        title = MDLabel(
            text="Conecte o WhatsApp",
            font_style="Headline",
            role="small",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )
        self.content_card.add_widget(title)

        # Instructions
        instructions = MDLabel(
            text="Para conectar, vamos gerar um QR Code que voce deve escanear com o WhatsApp.\n\n"
                 "Siga estes passos:\n\n"
                 "1. Abra o WhatsApp no seu celular\n"
                 "2. Toque em 'Mais opcoes' (⋮) > 'Dispositivos conectados'\n"
                 "3. Toque em 'Conectar um dispositivo'\n"
                 "4. Escaneie o QR Code que vamos gerar\n\n"
                 "Pronto! Seu bot estara conectado. 🎉",
            font_style="Body",
            role="medium",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        )
        self.content_card.add_widget(instructions)

        # Spacer
        self.content_card.add_widget(MDBoxLayout(size_hint_y=None, height=dp(16)))

        # Info card
        info_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(60),
            radius=[dp(12)],
            md_bg_color=(0.424, 0.388, 1.0, 0.15),
            padding=[dp(12)],
        )
        info_label = MDLabel(
            text="Dica: Seu celular precisa estar conectado a internet durante a conexao.",
            font_style="Label",
            role="small",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
        )
        info_card.add_widget(info_label)
        self.content_card.add_widget(info_card)

    def _build_step_3(self):
        """Step 3: Completion celebration."""
        # Celebration icon
        icon = MDLabel(
            text="🎉",
            font_size=sp(72),
            halign="center",
            size_hint_y=None,
            height=dp(90),
        )
        self.content_card.add_widget(icon)

        # Title
        title = MDLabel(
            text="Tudo Pronto!",
            font_style="Headline",
            role="small",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )
        self.content_card.add_widget(title)

        # Description
        desc = MDLabel(
            text="Seu bot esta configurado e pronto para conectar ao WhatsApp!\n\n"
                 "No proximo passo, voce vai:\n"
                 "• Conectar seu WhatsApp via QR Code\n"
                 "• Comecar a conversar com seus clientes\n"
                 "• Personalizar respostas e muito mais\n\n"
                 "Bora la? 🚀",
            font_style="Body",
            role="medium",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        )
        self.content_card.add_widget(desc)

    def _on_next(self, instance):
        if self.current_step == 0:
            # Save bot name
            name = self.bot_name_input.text.strip() if hasattr(self, 'bot_name_input') else ""
            if not name:
                name = "Meu Bot Flora"
            self.bot_name = name
            self.bot_personality = getattr(self, 'bot_personality', 'amigavel')

        if self.current_step < self.total_steps - 1:
            self._show_step(self.current_step + 1)
        else:
            # Finish onboarding - save bot config and go to dashboard
            from apps.client.main import save_token_data, load_token_data
            data = load_token_data() or {}
            data["bot_name"] = self.bot_name
            data["bot_personality"] = self.bot_personality
            data["onboarding_complete"] = True
            save_token_data(data)
            self.manager.current = "dashboard"

    def _on_back(self, instance):
        if self.current_step > 0:
            self._show_step(self.current_step - 1)
