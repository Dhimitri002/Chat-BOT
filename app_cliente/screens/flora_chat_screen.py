"""
Flora Chat Screen - Tela de Chat com a Flora AI
====================================================
Tela de chat dedicada com a Flora AI. Premium dark UI.

Features:
  - Bubbles de chat estilizadas (usuario direita, Flora esquerda)
  - Sugestoes contextuais baseadas na intencao detectada
  - Indicador de digitacao animado
  - Historico de conversa com scroll automatico
  - Integracao com API do backend via FloraService
"""

import threading
from datetime import datetime
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.app import MDApp


class FloraChatScreen(MDScreen):
    """Tela de chat com a Flora AI."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "flora_chat"
        self.session_id = ""
        self.suggestions = [
            "Criar meu primeiro bot",
            "Conectar WhatsApp",
            "Ver planos disponiveis",
            "Ajuda com comandos",
        ]
        self._is_loading = False
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
            height=dp(64),
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

        flora_title = MDBoxLayout(orientation="vertical", spacing=dp(0))
        flora_title.add_widget(MDLabel(
            text="Flora AI 🌸",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(24),
            bold=True,
        ))
        self.flora_status = MDLabel(
            text="Online - Pronta para ajudar!",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.SUCCESS),
            size_hint_y=None,
            height=dp(16),
        )
        flora_title.add_widget(self.flora_status)
        top_bar.add_widget(flora_title)

        top_bar.add_widget(MDLabel(text=""))

        clear_btn = MDFlatButton(
            text="Limpar",
            font_size="16sp",
            text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
            size_hint_x=None,
            width=dp(50),
        )
        clear_btn.bind(on_release=self._clear_history)
        top_bar.add_widget(clear_btn)

        root.add_widget(top_bar)

        # ---- Chat Messages ----
        self.messages_scroll = MDScrollView()
        self.messages_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(12),
            size_hint_y=None,
        )
        self.messages_box.bind(minimum_height=self.messages_box.setter("height"))
        self.messages_scroll.add_widget(self.messages_box)
        root.add_widget(self.messages_scroll)

        # ---- Typing Indicator ----
        self.typing_box = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
            padding=dp(12),
            opacity=0,
        )
        self.typing_label = MDLabel(
            text="Flora esta digitando",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            italic=True,
        )
        self.typing_box.add_widget(self.typing_label)
        self.typing_box.add_widget(MDLabel(
            text="🌸",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
        ))
        root.add_widget(self.typing_box)

        # ---- Quick Actions ----
        self.quick_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            padding=dp(8),
            size_hint_y=None,
            height=dp(100),
        )
        quick_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(36),
        )

        suggestion_labels = [
            ("Criar bot", "🤖", self._on_suggestion_bot),
            ("WhatsApp", "📱", self._on_suggestion_wa),
            ("Planos", "⭐", self._on_suggestion_plans),
            ("Suporte", "💬", self._on_suggestion_support),
        ]

        for label_text, icon_text, callback in suggestion_labels:
            btn = MDRectangleFlatButton(
                text=f"{icon_text} {label_text}",
                text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                line_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                size_hint_x=0.25,
                font_size="11sp",
            )
            btn.bind(on_release=callback)
            quick_row.add_widget(btn)

        self.quick_box.add_widget(quick_row)

        # Second row of suggestions
        quick_row2 = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(36),
        )
        more_suggestions = [
            ("Tutorial", "📖", self._on_suggestion_tutorial),
            ("Dicas", "💡", self._on_suggestion_tips),
            ("Onboarding", "🚀", self._on_suggestion_onboarding),
        ]
        for label_text, icon_text, callback in more_suggestions:
            btn = MDRectangleFlatButton(
                text=f"{icon_text} {label_text}",
                text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
                line_color=get_color_from_hex(ThemeColors.ACCENT),
                size_hint_x=0.25,
                font_size="11sp",
            )
            btn.bind(on_release=callback)
            quick_row2.add_widget(btn)

        self.quick_box.add_widget(quick_row2)
        root.add_widget(self.quick_box)

        # ---- Input Bar ----
        input_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            padding=dp(8),
            spacing=dp(8),
            md_bg_color=get_color_from_hex(ThemeColors.SECONDARY),
        )

        self.msg_input = MDTextField(
            hint_text="Pergunte a Flora...",
            mode="round",
            line_color_normal=get_color_from_hex(ThemeColors.ACCENT),
            line_color_focus=get_color_from_hex(ThemeColors.HIGHLIGHT),
            text_color_focus=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_x=0.8,
        )
        self.msg_input.bind(on_text_validate=self._send_message)
        input_bar.add_widget(self.msg_input)

        send_btn = MDRaisedButton(
            text="Enviar",
            md_bg_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_x=0.2,
            radius=[20],
        )
        send_btn.bind(on_release=self._send_message)
        input_bar.add_widget(send_btn)

        root.add_widget(input_bar)

        # Welcome message
        Clock.schedule_once(self._show_welcome, 0.5)

    def _show_welcome(self, *args):
        """Mensagem de boas-vindas da Flora."""
        app = MDApp.get_running_app()
        user_name = getattr(app, 'user_name', "") if app else ""

        welcome = (
            f"Ola{f' , {user_name}' if user_name else ''}! Eu sou a Flora! 🌸\n\n"
            "Sou sua assistente inteligente da plataforma. "
            "Posso te ajudar a:\n\n"
            "- 🤖 **Criar bots** com personalidades customizadas\n"
            "- 📱 **Conectar o WhatsApp** ao seu bot\n"
            "- ⭐ **Escolher o melhor plano** para voce\n"
            "- 🔧 **Resolver problemas** tecnicos\n\n"
            "O que voce gostaria de fazer hoje?"
        )
        self._add_message(welcome, is_sent=False)
        self._update_suggestions([
            "🤖 Criar meu primeiro bot",
            "📱 Conectar WhatsApp",
            "⭐ Ver planos",
            "📖 Ver tutorial",
        ])

    def _update_suggestions(self, suggestions):
        """Atualiza botoes de sugestao."""
        self.suggestions = suggestions

    def _add_message(self, text, is_sent=True):
        """Adiciona mensagem ao chat."""
        from app_cliente.main import ThemeColors

        container = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            padding=dp(8),
        )

        timestamp = datetime.now().strftime("%H:%M")

        if is_sent:
            container.add_widget(MDLabel(text=""))
            bubble = self._create_bubble(text, True, "Voce", timestamp)
            container.add_widget(bubble)
        else:
            avatar = MDBoxLayout(
                size_hint_x=None,
                width=dp(32),
                padding=dp(4),
            )
            avatar.add_widget(MDLabel(
                text="🌸",
                font_style="H6",
                halign="center",
            ))
            container.add_widget(avatar)
            bubble = self._create_bubble(text, False, "Flora", timestamp)
            container.add_widget(bubble)

        container.opacity = 0
        self.messages_box.add_widget(container)
        anim = Animation(opacity=1, duration=0.3)
        anim.start(container)
        Clock.schedule_once(lambda dt: self._scroll_bottom(), 0.1)

    def _create_bubble(self, text, is_sent, sender_name, timestamp):
        """Cria bolha de mensagem."""
        from app_cliente.main import ThemeColors

        radius_val = [18, 18, 4, 18] if is_sent else [18, 18, 18, 4]
        bg_color = ThemeColors.HIGHLIGHT if is_sent else ThemeColors.SECONDARY

        bubble = MDCard(
            orientation="vertical",
            spacing=dp(2),
            padding=dp(12),
            radius=radius_val,
            elevation=2,
            md_bg_color=get_color_from_hex(bg_color),
            size_hint=(None, None),
            width=dp(240),
        )

        if not is_sent:
            bubble.add_widget(MDLabel(
                text="🌸 " + sender_name,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                size_hint_y=None,
                height=dp(16),
                bold=True,
            ))

        msg_label = MDLabel(
            text=text,
            font_style="Body1",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            text_size=(dp(220), None),
        )
        msg_label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", val[1] + dp(4))
        )
        bubble.add_widget(msg_label)

        bubble.add_widget(MDLabel(
            text=timestamp,
            font_style="Caption",
            halign="right",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
            size_hint_y=None,
            height=dp(14),
        ))

        mh = dp(16) + msg_label.texture_size[1] + dp(14) + dp(28) + dp(8)
        if not is_sent:
            mh += dp(18)
        bubble.height = mh + dp(24)

        return bubble

    def _send_message(self, *args):
        """Envia mensagem para Flora AI."""
        text = self.msg_input.text.strip()
        if not text or self._is_loading:
            return

        self._is_loading = True
        self._add_message(text, is_sent=True)
        self.msg_input.text = ""
        self._show_typing()

        # Desabilitar input enquanto processa
        self.msg_input.disabled = True
        self.flora_status.text = "Pensando..."
        self.flora_status.text_color = get_color_from_hex("#f9a825")

        def _do():
            try:
                from app_cliente.services.api_client import api
                result = api.flora_chat(text, session_id=self.session_id or None)

                # Atualizar session_id da resposta
                if result.get("session_id"):
                    self.session_id = result["session_id"]

                response = result.get("response", "Desculpe, nao entendi. Pode repetir?")
                suggestions = result.get("suggestions", [])
                intent = result.get("intent", "")

                Clock.schedule_once(
                    lambda dt: self._receive_message(response, suggestions, intent), 0
                )
            except Exception as e:
                err_msg = (f"😔 Ocorreu um erro ao falar com a Flora.\n\n"
                          f"Verifique sua conexao e tente novamente.")
                Clock.schedule_once(
                    lambda dt: self._receive_message(err_msg, [], ""), 0
                )

        threading.Thread(target=_do, daemon=True).start()

    def _receive_message(self, text, suggestions, intent=""):
        """Recebe resposta da Flora."""
        self._hide_typing()
        self._is_loading = False
        self.msg_input.disabled = False
        self.flora_status.text = "Online - Pronta para ajudar!"
        self.flora_status.text_color = get_color_from_hex("#4caf50")

        self._add_message(text, is_sent=False)

        # Atualizar sugestoes baseado na intencao
        if intent:
            intent_suggestions = self._get_suggestions_for_intent(intent)
            if intent_suggestions:
                self._update_suggestions(intent_suggestions)
        elif suggestions:
            self._update_suggestions(suggestions)

    @staticmethod
    def _get_suggestions_for_intent(intent: str) -> list:
        """Retorna sugestoes baseado na intencao detectada."""
        intent_map = {
            "onboarding": [
                "Como criar meu primeiro bot?",
                "Como conectar o WhatsApp?",
                "Quais planos estao disponiveis?",
            ],
            "bot_config": [
                "Como definir a personalidade do bot?",
                "Como adicionar intencoes?",
                "Como ativar meu bot?",
            ],
            "whatsapp": [
                "Como escanear o QR Code?",
                "Meu WhatsApp desconectou, o que fazer?",
                "Posso conectar mais de um numero?",
            ],
            "billing": [
                "Qual o melhor plano para mim?",
                "Como fazer upgrade?",
                "Voces aceitam Pix?",
            ],
            "technical": [
                "Bot nao esta respondendo",
                "Erro ao conectar WhatsApp",
                "Como ver logs do bot?",
            ],
        }
        return intent_map.get(intent, [])

    def _show_typing(self):
        """Mostra indicador de digitando."""
        self.typing_box.opacity = 1
        self._dots = 0

        def _animate(*args):
            self._dots = (self._dots + 1) % 4
            self.typing_label.text = "Flora esta digitando" + "." * self._dots

        self._typing_clock = Clock.schedule_interval(_animate, 0.4)

    def _hide_typing(self):
        """Esconde indicador de digitando."""
        self.typing_box.opacity = 0
        if hasattr(self, '_typing_clock'):
            self._typing_clock.cancel()

    def _scroll_bottom(self):
        """Scroll para o final."""
        if hasattr(self, 'messages_box'):
            # ScrollView scroll
            sv = self.messages_scroll
            if sv:
                sv.scroll_y = 0

    def _clear_history(self, *args):
        """Limpa historico de chat."""
        self.messages_box.clear_widgets()
        self._add_message(
            "Historico limpo! 🧹\nComo posso te ajudar agora?",
            is_sent=False,
        )

    # Quick suggestion handlers
    def _on_suggestion_bot(self, *args):
        self.msg_input.text = "Como criar meu primeiro bot?"
        self._send_message()

    def _on_suggestion_wa(self, *args):
        self.msg_input.text = "Como conectar o WhatsApp?"
        self._send_message()

    def _on_suggestion_plans(self, *args):
        self.msg_input.text = "Quais planos estao disponiveis?"
        self._send_message()

    def _on_suggestion_support(self, *args):
        self.msg_input.text = "Preciso de suporte tecnico"
        self._send_message()

    def _on_suggestion_tutorial(self, *args):
        self.msg_input.text = "Me mostre um tutorial basico"
        self._send_message()

    def _on_suggestion_tips(self, *args):
        self.msg_input.text = "Quais dicas voce tem para comecar?"
        self._send_message()

    def _on_suggestion_onboarding(self, *args):
        self.manager.transition.direction = "left"
        self.manager.current = "onboarding"

    def _go_back(self, *args):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_enter(self):
        pass
