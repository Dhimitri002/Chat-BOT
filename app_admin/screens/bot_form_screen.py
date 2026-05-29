# ═══════════════════════════════════════════════════════════════
# Flora Platform — Formulário de Bot
# ═══════════════════════════════════════════════════════════════

from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.scrollview import ScrollView

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.dialog import MDDialog
from kivymd.toast import toast

from apps.shared.api_client import api


class BotFormScreen(Screen):
    """Tela de criação/edição de bot."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "bot_form"
        self._bot_id = None
        self._dialog = None
        self._loading = False
        self._build()

    def _build(self):
        """Constrói o formulário."""
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

        self.title_lbl = MDLabel(
            text="Novo Bot",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6",
            bold=True,
        )

        spacer = MDBoxLayout(size_hint_x=1)
        toolbar.add_widget(back_btn)
        toolbar.add_widget(self.title_lbl)
        toolbar.add_widget(spacer)
        main_layout.add_widget(toolbar)

        # ── Formulário ──────────────────────────────────────────
        scroll = ScrollView()
        form = MDBoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(16),
            size_hint_y=None,
        )
        form.bind(minimum_height=form.setter("height"))

        # Card do formulário
        form_card = MDCard(
            orientation="vertical",
            radius=[dp(16)],
            elevation=2,
            padding=dp(20),
            spacing=dp(12),
            size_hint_y=None,
            md_bg_color=(0.11, 0.165, 0.298, 1),
        )
        form_card.bind(minimum_height=form_card.setter("height"))

        # Nome
        form_card.add_widget(MDLabel(
            text="Nome do Bot *",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        ))
        self.name_field = MDTextField(
            hint_text="Ex: Assistente Virtual",
            mode="round",
            radius=[dp(10)],
            size_hint_y=None,
            height=dp(52),
            hint_text_color_normal=(0.376, 0.49, 0.545, 1),
            text_color_normal=(1, 1, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            line_color_normal=(0.227, 0.294, 0.431, 1),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            fill_color_normal=(0.055, 0.106, 0.243, 1),
        )
        form_card.add_widget(self.name_field)

        # Descrição
        form_card.add_widget(MDLabel(
            text="Descrição",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        ))
        self.desc_field = MDTextField(
            hint_text="Descreva o propósito do bot...",
            mode="round",
            radius=[dp(10)],
            multiline=True,
            size_hint_y=None,
            height=dp(80),
            hint_text_color_normal=(0.376, 0.49, 0.545, 1),
            text_color_normal=(1, 1, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            line_color_normal=(0.227, 0.294, 0.431, 1),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            fill_color_normal=(0.055, 0.106, 0.243, 1),
        )
        form_card.add_widget(self.desc_field)

        # Personalidade
        form_card.add_widget(MDLabel(
            text="Personalidade",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        ))
        self.personality_field = MDTextField(
            hint_text="Ex: amigável, profissional, divertido",
            mode="round",
            radius=[dp(10)],
            size_hint_y=None,
            height=dp(52),
            hint_text_color_normal=(0.376, 0.49, 0.545, 1),
            text_color_normal=(1, 1, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            line_color_normal=(0.227, 0.294, 0.431, 1),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            fill_color_normal=(0.055, 0.106, 0.243, 1),
        )
        form_card.add_widget(self.personality_field)

        # Mensagem de Boas-vindas
        form_card.add_widget(MDLabel(
            text="Mensagem de Boas-vindas",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        ))
        self.welcome_field = MDTextField(
            hint_text="Olá! Como posso te ajudar?",
            mode="round",
            radius=[dp(10)],
            multiline=True,
            size_hint_y=None,
            height=dp(70),
            hint_text_color_normal=(0.376, 0.49, 0.545, 1),
            text_color_normal=(1, 1, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            line_color_normal=(0.227, 0.294, 0.431, 1),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            fill_color_normal=(0.055, 0.106, 0.243, 1),
        )
        form_card.add_widget(self.welcome_field)

        # Mensagem de Despedida
        form_card.add_widget(MDLabel(
            text="Mensagem de Despedida",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        ))
        self.farewell_field = MDTextField(
            hint_text="Até mais! Foi um prazer ajudar.",
            mode="round",
            radius=[dp(10)],
            multiline=True,
            size_hint_y=None,
            height=dp(70),
            hint_text_color_normal=(0.376, 0.49, 0.545, 1),
            text_color_normal=(1, 1, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            line_color_normal=(0.227, 0.294, 0.431, 1),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            fill_color_normal=(0.055, 0.106, 0.243, 1),
        )
        form_card.add_widget(self.farewell_field)

        # Prompt do Sistema
        form_card.add_widget(MDLabel(
            text="Prompt do Sistema (System Prompt)",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        ))
        self.prompt_field = MDTextField(
            hint_text="Instruções para a IA...",
            mode="round",
            radius=[dp(10)],
            multiline=True,
            size_hint_y=None,
            height=dp(100),
            hint_text_color_normal=(0.376, 0.49, 0.545, 1),
            text_color_normal=(1, 1, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            line_color_normal=(0.227, 0.294, 0.431, 1),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            fill_color_normal=(0.055, 0.106, 0.243, 1),
        )
        form_card.add_widget(self.prompt_field)

        form.add_widget(form_card)

        # ── Botões de Ação ──────────────────────────────────────
        actions = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(56),
            padding=[dp(0), dp(8)],
        )

        cancel_btn = MDFlatButton(
            text="Cancelar",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Button",
            size_hint_x=0.4,
            on_release=lambda x: self._go_back(),
        )

        self.save_btn = MDRaisedButton(
            text="Salvar",
            md_bg_color=(0.424, 0.388, 1.0, 1),
            text_color=(1, 1, 1, 1),
            font_style="Button",
            radius=[dp(12)],
            size_hint_x=0.6,
            on_release=lambda x: self._save(),
        )

        actions.add_widget(cancel_btn)
        actions.add_widget(self.save_btn)
        form.add_widget(actions)

        # Loading
        self._save_spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={"center_x": 0.5},
            active=False,
        )
        form.add_widget(self._save_spinner)

        scroll.add_widget(form)
        main_layout.add_widget(scroll)
        self.add_widget(main_layout)

    def load_bot(self, bot):
        """Carrega dados de um bot para edição."""
        self._bot_id = bot.get("id")
        self.title_lbl.text = "Editar Bot"
        self.name_field.text = bot.get("name", "")
        self.desc_field.text = bot.get("description", "")
        self.personality_field.text = bot.get("personality", "")
        self.welcome_field.text = bot.get("welcome_message", "")
        self.farewell_field.text = bot.get("farewell_message", "")
        self.prompt_field.text = bot.get("system_prompt", "")

    def _save(self):
        """Salva o bot."""
        name = self.name_field.text.strip()
        if not name:
            toast("O nome do bot é obrigatório.")
            return

        data = {
            "name": name,
            "description": self.desc_field.text.strip(),
            "personality": self.personality_field.text.strip() or "friendly",
            "welcome_message": self.welcome_field.text.strip() or "Ola! Como posso te ajudar?",
            "farewell_message": self.farewell_field.text.strip() or "Ate mais!",
            "system_prompt": self.prompt_field.text.strip(),
        }

        self._loading = True
        self.save_btn.opacity = 0
        self.save_btn.disabled = True
        self._save_spinner.active = True

        if self._bot_id:
            api.put_async(f"/bots/{self._bot_id}", self._on_save_result, data)
        else:
            api.post_async("/bots", self._on_save_result, data)

    def _on_save_result(self, result):
        """Callback do resultado do salvamento."""
        Clock.schedule_once(lambda dt: self._handle_save(result), 0)

    def _handle_save(self, result):
        """Processa o resultado do salvamento."""
        self._loading = False
        self.save_btn.opacity = 1
        self.save_btn.disabled = False
        self._save_spinner.active = False

        if result.get("error"):
            toast(result.get("message", "Erro ao salvar bot."))
        else:
            toast("Bot salvo com sucesso!")
            self._go_back()

    def _go_back(self):
        """Volta para a tela de bots."""
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "bots"

    def on_enter(self, *args):
        """Limpa o formulário se for novo bot."""
        if not self._bot_id:
            self.title_lbl.text = "Novo Bot"
            self.name_field.text = ""
            self.desc_field.text = ""
            self.personality_field.text = ""
            self.welcome_field.text = ""
            self.farewell_field.text = ""
            self.prompt_field.text = ""
        return super().on_enter(*args)

    def on_leave(self, *args):
        """Limpa o ID ao sair."""
        self._bot_id = None
        self.title_lbl.text = "Novo Bot"
        return super().on_leave(*args)
