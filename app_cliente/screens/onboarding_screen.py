"""
Flora Platform — Onboarding Screen
=====================================
Multi-step onboarding flow (4 steps) shown after registration.
Introduces the user to the platform features.
"""
from kivy.app import App
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.metrics import dp

ONBOARDING_STEPS = [
    {
        "emoji": "",
        "title": "Bem-vindo ao Flora!",
        "desc": "Sua plataforma de chatbots para WhatsApp. Vamos configurar tudo em poucos passos.",
        "color": (0.914, 0.271, 0.376, 1),
    },
    {
        "emoji": "",
        "title": "Crie seu primeiro bot",
        "desc": "Configure um chatbot com personalidade, comandos e respostas inteligentes em minutos.",
        "color": (0.31, 0.8, 0.639, 1),
    },
    {
        "emoji": "",
        "title": "Conecte ao WhatsApp",
        "desc": "Escaneie um QR code e seu bot estará respondendo no WhatsApp automaticamente.",
        "color": (0.914, 0.271, 0.376, 1),
    },
    {
        "emoji": "",
        "title": "Flora AI te ajuda",
        "desc": "Nossa IA Flora está pronta para te ajudar com qualquer dúvida. Vamos começar!",
        "color": (0.31, 0.8, 0.639, 1),
    },
]

Builder.load_string(
    """
<OnboardingScreen>:
    name: "onboarding"
    canvas.before:
        Color:
            rgba: 0.102, 0.102, 0.18, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: "vertical"
        padding: dp(32)
        spacing: dp(20)

        # Top bar with skip
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(8)

            # Step indicators
            BoxLayout:
                size_hint_x: 0.7
                spacing: dp(6)
                padding: dp(0), dp(12)
                canvas.before:
                    Color:
                        rgba: 0.137, 0.129, 0.243, 0.5
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(10)]

                Label:
                    text: "Passo " + str(root.current_step + 1) + " de " + str(root.total_steps)
                    font_size: "12sp"
                    color: 0.6, 0.6, 0.7, 1

            Widget:
                size_hint_x: 0.1

            # Skip button
            MDFlatButton:
                text: "Pular"
                font_size: "13sp"
                size_hint_x: None
                width: dp(60)
                text_color: 0.5, 0.5, 0.6, 1
                on_release: root.skip_onboarding()

        # Content area
        BoxLayout:
            orientation: "vertical"
            spacing: dp(24)

            Widget:
                size_hint_y: 0.1

            # Emoji
            Label:
                text: root.step_emoji
                font_size: "72sp"
                size_hint_y: None
                height: dp(90)

            # Title
            Label:
                text: root.step_title
                font_size: "26sp"
                bold: True
                color: 1, 1, 1, 1
                size_hint_y: None
                height: dp(40)
                text_size: self.width, None
                halign: "center"

            # Description
            Label:
                text: root.step_desc
                font_size: "14sp"
                color: 0.6, 0.6, 0.7, 1
                text_size: self.width, None
                halign: "center"
                valign: "top"
                size_hint_y: None
                height: dp(60)

            Widget:
                size_hint_y: 0.2

        # Progress dots
        BoxLayout:
            size_hint_y: None
            height: dp(12)
            spacing: dp(8)
            pos_hint: {"center_x": 0.5}
            size_hint_x: None

            # Dots will be added dynamically

        # Bottom buttons
        BoxLayout:
            size_hint_y: None
            height: dp(52)
            spacing: dp(12)

            # Back button
            MDRaisedButton:
                text: "Voltar"
                size_hint_x: 0.35
                size_hint_y: None
                height: dp(52)
                md_bg_color: 0.137, 0.129, 0.243, 0.6
                text_color: 0.7, 0.7, 0.8, 1
                line_color: 0.2, 0.2, 0.3, 1
                radius: [dp(14)]
                on_release: root.prev_step()
                opacity: 1 if root.current_step > 0 else 0
                disabled: root.current_step == 0

            # Next button
            MDRaisedButton:
                text: root.next_button_text
                size_hint_x: 0.65
                size_hint_y: None
                height: dp(52)
                font_size: "16sp"
                bold: True
                md_bg_color: 0.914, 0.271, 0.376, 1
                text_color: 1, 1, 1, 1
                line_color: 0.914, 0.271, 0.376, 1
                radius: [dp(14)]
                on_release: root.next_step()
"""
)


class OnboardingScreen(Screen):
    """Multi-step onboarding flow."""

    current_step = NumericProperty(0)
    total_steps = NumericProperty(4)
    step_emoji = StringProperty("")
    step_title = StringProperty("")
    step_desc = StringProperty("")
    next_button_text = StringProperty("Proximo")

    def on_enter(self):
        """Initialize onboarding."""
        self.current_step = 0
        self._update_step()

    def _update_step(self):
        """Update UI for current step."""
        step = ONBOARDING_STEPS[self.current_step]
        self.step_emoji = step["emoji"]
        self.step_title = step["title"]
        self.step_desc = step["desc"]
        self.next_button_text = "Comecar!" if self.current_step == self.total_steps - 1 else "Proximo"

    def next_step(self):
        """Go to next step or finish."""
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
            self._update_step()
        else:
            self._finish()

    def prev_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_step()

    def skip_onboarding(self):
        """Skip onboarding and go to home."""
        self._finish()

    def _finish(self):
        """Complete onboarding and navigate to home."""
        self.manager.current = "home"
