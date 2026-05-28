# ═══════════════════════════════════════════════════════════════
# Flora Platform — Welcome Screen
# ═══════════════════════════════════════════════════════════════

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout


class WelcomeScreen(MDScreen):
    """Welcome screen for first-time users with a 3-step flow."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_page = 0
        self.total_pages = 3
        self._build_ui()

    def _build_ui(self):
        self.md_bg_color = (0.102, 0.102, 0.180, 1)

        main_layout = MDFloatLayout()

        # Top bar with skip button
        top_bar = MDBoxLayout(
            size_hint=(1, None),
            height=dp(56),
            pos_hint={"top": 1},
            padding=[dp(16), dp(8)],
        )
        skip_btn = MDButton(
            MDButtonText(text="Pular", theme_text_color="Custom", text_color=(0.7, 0.7, 0.75, 1)),
            style="text",
            pos_hint={"right": 1, "center_y": 0.5},
            on_release=self._on_skip,
        )
        top_bar.add_widget(skip_btn)
        main_layout.add_widget(top_bar)

        # Content area
        self.content_card = MDCard(
            orientation="vertical",
            size_hint=(0.85, 0.65),
            pos_hint={"center_x": 0.5, "center_y": 0.48},
            radius=[dp(24)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(24), dp(20)],
            spacing=dp(16),
            elevation=4,
        )

        # Page content
        self.page_label = MDLabel(
            text="",
            font_style="Headline",
            role="small",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(60),
        )
        self.content_card.add_widget(self.page_label)

        self.emoji_label = MDLabel(
            text="",
            font_size=sp(64),
            halign="center",
            size_hint_y=None,
            height=dp(80),
        )
        self.content_card.add_widget(self.emoji_label)

        self.desc_label = MDLabel(
            text="",
            font_style="Body",
            role="large",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
            size_hint_y=None,
            adaptive_height=True,
        )
        self.content_card.add_widget(self.desc_label)

        main_layout.add_widget(self.content_card)

        # Page indicator dots
        dots_layout = MDBoxLayout(
            size_hint=(1, None),
            height=dp(24),
            pos_hint={"center_x": 0.5, "y": 0.18},
            spacing=dp(8),
            padding=[dp(0)],
        )
        dots_layout.bind(size=self._center_dots)
        self.dots = []
        for i in range(self.total_pages):
            dot = MDCard(
                size_hint=(None, None),
                size=(dp(10), dp(10)),
                radius=[dp(5)],
                md_bg_color=(0.424, 0.388, 1.0, 1) if i == 0 else (0.3, 0.3, 0.4, 1),
            )
            self.dots.append(dot)
            dots_layout.add_widget(dot)
        self.dots_layout = dots_layout
        main_layout.add_widget(dots_layout)

        # Bottom buttons
        bottom_box = MDBoxLayout(
            size_hint=(0.85, None),
            height=dp(56),
            pos_hint={"center_x": 0.5, "y": 0.06},
            spacing=dp(12),
        )

        self.back_btn = MDButton(
            MDButtonText(text="Voltar"),
            style="outlined",
            size_hint_x=0.4,
            on_release=self._on_back,
        )
        self.back_btn.line_color = (0.424, 0.388, 1.0, 1)
        self.back_btn.md_bg_color = (0, 0, 0, 0)
        self.back_btn.text_color = (0.424, 0.388, 1.0, 1)
        bottom_box.add_widget(self.back_btn)

        self.next_btn = MDButton(
            MDButtonText(text="Começar"),
            style="filled",
            size_hint_x=0.6,
            md_bg_color=(0.424, 0.388, 1.0, 1),
            on_release=self._on_next,
        )
        bottom_box.add_widget(self.next_btn)

        main_layout.add_widget(bottom_box)
        self.add_widget(main_layout)

        # Set initial page
        self._show_page(0)

    def _center_dots(self, instance, value):
        instance.pos_hint = {"center_x": 0.5, "y": 0.18}

    def _show_page(self, page: int):
        """Show the given welcome page."""
        self.current_page = page
        pages = [
            {
                "title": "Bem-vinda à Flora! 🌸",
                "emoji": "🌸",
                "desc": "A Flora é a plataforma mais fácil para criar e gerenciar seu chatbot no WhatsApp. "
                         "Automatize respostas, converse com clientes e muito mais — tudo em um só lugar."
            },
            {
                "title": "Configure em Minutos ⚡",
                "emoji": "⚡",
                "desc": "Em apenas 3 passos seu bot estará no ar: cadastre-se, conecte o WhatsApp e defina "
                         "o comportamento do seu bot. Sem complicação, sem código."
            },
            {
                "title": "Flora AI ao seu Lado 🤖",
                "emoji": "🤖",
                "desc": "Nossa assistente Flora AI te ajuda em cada etapa. Tire dúvidas, personalize "
                         "respostas e otimize seu bot com inteligência artificial."
            },
        ]

        p = pages[page]
        self.page_label.text = p["title"]
        self.emoji_label.text = p["emoji"]
        self.desc_label.text = p["desc"]

        # Update dots
        for i, dot in enumerate(self.dots):
            dot.md_bg_color = (0.424, 0.388, 1.0, 1) if i == page else (0.3, 0.3, 0.4, 1)

        # Update buttons
        if page == 0:
            self.back_btn.text = ""
            self.back_btn.disabled = True
            self.back_btn.opacity = 0
        else:
            self.back_btn.text = "Voltar"
            self.back_btn.disabled = False
            self.back_btn.opacity = 1

        if page == self.total_pages - 1:
            self.next_btn.children[0].children[0].text = "Comecar"
        else:
            self.next_btn.children[0].children[0].text = "Proximo"

    def _on_next(self, instance):
        if self.current_page < self.total_pages - 1:
            self._show_page(self.current_page + 1)
        else:
            # Mark welcome as seen
            from apps.client.main import load_token_data, save_token_data
            data = load_token_data() or {}
            data["seen_welcome"] = True
            save_token_data(data)
            self.manager.current = "license"

    def _on_back(self, instance):
        if self.current_page > 0:
            self._show_page(self.current_page - 1)

    def _on_skip(self, instance):
        from apps.client.main import load_token_data, save_token_data
        data = load_token_data() or {}
        data["seen_welcome"] = True
        save_token_data(data)
        self.manager.current = "license"
