"""Support Screen — Tela de suporte e ajuda."""
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView


class SupportScreen(MDScreen):
    """Tela de suporte ao cliente."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "support"
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
            text="←",
            font_size="24sp",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_x=None,
            width=dp(48),
        )
        back_btn.bind(on_release=self._go_back)
        top_bar.add_widget(back_btn)

        top_bar.add_widget(MDLabel(
            text="💬 Suporte",
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
            padding=dp(16),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))
        scroll.add_widget(content)
        root.add_widget(scroll)

        # ---- Quick Actions ----
        quick_card = MDCard(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(16),
            radius=[16],
            elevation=3,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
            height=dp(120),
        )

        quick_card.add_widget(MDLabel(
            text="Como podemos ajudar?",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        ))

        quick_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(44),
        )

        flora_btn = MDRaisedButton(
            text="🌸 Falar com Flora",
            md_bg_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_x=0.5,
            radius=[12],
        )
        flora_btn.bind(on_release=self._go_to_flora)
        quick_row.add_widget(flora_btn)

        ticket_btn = MDRaisedButton(
            text="📝 Abrir Ticket",
            md_bg_color=get_color_from_hex(ThemeColors.ACCENT),
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_x=0.5,
            radius=[12],
        )
        ticket_btn.bind(on_release=self._show_ticket_form)
        quick_row.add_widget(ticket_btn)

        quick_card.add_widget(quick_row)
        content.add_widget(quick_card)

        # ---- FAQ Section ----
        faq_card = MDCard(
            orientation="vertical",
            spacing=dp(4),
            padding=dp(16),
            radius=[16],
            elevation=2,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
        )
        faq_card.bind(minimum_height=faq_card.setter("height"))

        faq_card.add_widget(MDLabel(
            text="Perguntas Frequentes",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        ))

        faqs = [
            ("Como criar um bot?",
             "Va em 'Criar Bot' no menu principal. Escolha um nome, "
             "personalidade e mensagem de boas-vindas. E facil!"),
            ("Como conectar o WhatsApp?",
             "Va em 'Conectar WhatsApp', gere o QR Code e escaneie "
             "com o app do WhatsApp no seu celular."),
            ("Quantos bots posso criar?",
             "Depende do seu plano. No gratuito: 1 bot. No Pro: 10 bots. "
             "No Enterprise: bots ilimitados!"),
            ("O bot funciona 24 horas?",
             "Sim! Uma vez conectado, seu bot responde automaticamente "
             "a qualquer hora do dia ou da noite."),
            ("Posso personalizar as respostas?",
             "Sim! Voce pode treinar seu bot com intencoes, respostas "
             "personalizadas e muito mais."),
            ("Como trocar de plano?",
             "Va em 'Planos' no menu e escolha o plano desejado. "
             "A troca e instantanea!"),
        ]

        for question, answer in faqs:
            faq_item = MDBoxLayout(
                orientation="vertical",
                spacing=dp(2),
                size_hint_y=None,
                height=dp(60),
            )
            faq_item.add_widget(MDLabel(
                text=f"Q: {question}",
                font_style="Subtitle2",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
                size_hint_y=None,
                height=dp(20),
                bold=True,
            ))
            faq_item.add_widget(MDLabel(
                text=f"A: {answer}",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
                size_hint_y=None,
                height=dp(36),
                text_size=(dp(280), None),
            ))
            faq_card.add_widget(faq_item)

        content.add_widget(faq_card)

        # ---- Contact Form ----
        form_card = MDCard(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(20),
            radius=[16],
            elevation=3,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
        )
        form_card.bind(minimum_height=form_card.setter("height"))

        form_card.add_widget(MDLabel(
            text="Enviar Mensagem",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        ))

        # Category
        cat_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(36),
        )
        cat_row.add_widget(MDLabel(
            text="Categoria:",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_SECONDARY),
            size_hint_x=None,
            width=dp(80),
        ))
        self.category_btn = MDRectangleFlatButton(
            text="Geral",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            line_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_x=0.4,
        )
        cat_row.add_widget(self.category_btn)
        form_card.add_widget(cat_row)

        # Subject
        self.subject_input = MDTextField(
            hint_text="Assunto",
            helper_text="Resuma seu problema em uma frase",
            helper_text_mode="on_focus",
            icon_left="text-short",
            mode="round",
            line_color_normal=get_color_from_hex(ThemeColors.ACCENT),
            line_color_focus=get_color_from_hex(ThemeColors.HIGHLIGHT),
            text_color_focus=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(56),
        )
        form_card.add_widget(self.subject_input)

        # Message
        self.message_input = MDTextField(
            hint_text="Sua mensagem",
            helper_text="Descreva seu problema com detalhes",
            helper_text_mode="on_focus",
            icon_left="message-text",
            mode="round",
            multiline=True,
            line_color_normal=get_color_from_hex(ThemeColors.ACCENT),
            line_color_focus=get_color_from_hex(ThemeColors.HIGHLIGHT),
            text_color_focus=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(100),
        )
        form_card.add_widget(self.message_input)

        send_btn = MDRaisedButton(
            text="📤 Enviar Mensagem",
            md_bg_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            text_color=get_color_from_hex(ThemeColors.TEXT_PRIMARY),
            size_hint_y=None,
            height=dp(44),
            radius=[12],
        )
        send_btn.bind(on_release=self._send_message)
        form_card.add_widget(send_btn)

        self.status_label = MDLabel(
            text="",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
            size_hint_y=None,
            height=dp(16),
        )
        form_card.add_widget(self.status_label)

        content.add_widget(form_card)

        # ---- Ticket History ----
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
            text="Seus Tickets",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        ))

        self.tickets_label = MDLabel(
            text="Nenhum ticket aberto. Tudo funcionando bem! 🎉",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.TEXT_HINT),
        )
        history_card.add_widget(self.tickets_label)
        content.add_widget(history_card)

        # ---- Knowledge Base Links ----
        kb_card = MDCard(
            orientation="vertical",
            spacing=dp(4),
            padding=dp(16),
            radius=[16],
            elevation=2,
            md_bg_color=get_color_from_hex(ThemeColors.CARD),
            size_hint_y=None,
            height=dp(120),
        )

        kb_card.add_widget(MDLabel(
            text="Base de Conhecimento",
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
            size_hint_y=None,
            height=dp(28),
            bold=True,
        ))

        kb_links = [
            ("Documentacao da API", "📚"),
            ("Guia de Inicio Rapido", "🚀"),
            ("Tutoriais em Video", "🎥"),
            ("Blog e Novidades", "📰"),
        ]

        for link_text, link_icon in kb_links:
            link_btn = MDFlatButton(
                text=f"{link_icon} {link_text}",
                text_color=get_color_from_hex(ThemeColors.HIGHLIGHT),
                size_hint_y=None,
                height=dp(24),
            )
            kb_card.add_widget(link_btn)

        content.add_widget(kb_card)
        content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(20)))

    def _show_ticket_form(self, *args):
        """Mostra o formulario de ticket (scroll para ele)."""
        pass

    def _send_message(self, *args):
        """Envia mensagem de suporte."""
        subject = self.subject_input.text.strip()
        message = self.message_input.text.strip()

        if not subject or not message:
            self.status_label.text = "Preencha assunto e mensagem!"
            self.status_label.text_color = get_color_from_hex("#ef5350")
            return

        self.status_label.text = "Enviando..."
        self.status_label.text_color = get_color_from_hex("#4ecca3")

        def _do():
            try:
                from app_cliente.services.api_client import api
                result = api.create_ticket(
                    subject=subject,
                    message=message,
                    category="general",
                )
                Clock.schedule_once(
                    lambda dt: self._on_ticket_sent(result), 0
                )
            except Exception as e:
                Clock.schedule_once(
                    lambda dt: self._on_send_error(str(e)), 0
                )

        import threading
        threading.Thread(target=_do, daemon=True).start()

    def _on_ticket_sent(self, result):
        """Ticket enviado com sucesso."""
        self.status_label.text = "Mensagem enviada! Responderemos em breve! 🎉"
        self.status_label.text_color = get_color_from_hex("#4ecca3")
        self.subject_input.text = ""
        self.message_input.text = ""
        self.tickets_label.text = f"Ticket #{result.get('id', 'N/A')} aberto"

    def _on_send_error(self, error_msg):
        """Erro ao enviar."""
        self.status_label.text = f"Erro: {error_msg}"
        self.status_label.text_color = get_color_from_hex("#ef5350")

    def _go_to_flora(self, *args):
        self.manager.transition.direction = "left"
        self.manager.current = "flora_chat"

    def _go_back(self, *args):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_enter(self):
        self.status_label.text = ""
