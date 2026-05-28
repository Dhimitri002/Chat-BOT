# ═══════════════════════════════════════════════════════════════
# Flora Platform — Splash Screen
# ═══════════════════════════════════════════════════════════════

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty

from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.fitimage import FitImage


class SplashScreen(MDScreen):
    """Beautiful splash screen with animated Flora logo."""

    opacity_val = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        from kivymd.uix.floatlayout import MDFloatLayout
        from kivymd.uix.card import MDCard

        layout = MDFloatLayout()
        layout.md_bg_color = (0.102, 0.102, 0.180, 1)  # FLORA_BG

        # Center content
        center_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            pos_hint={"center_x": 0.5, "center_y": 0.52},
            size_hint=(0.7, None),
            height=dp(260),
            adaptive_height=True,
        )

        # Logo area - colored card with flower emoji
        logo_card = MDCard(
            size_hint=(None, None),
            size=(dp(120), dp(120)),
            pos_hint={"center_x": 0.5},
            radius=[dp(60)],
            md_bg_color=(0.424, 0.388, 1.0, 1),
            elevation=8,
        )
        logo_inner = MDBoxLayout(
            orientation="vertical",
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        logo_label = MDLabel(
            text="🌸",
            font_size=sp(52),
            halign="center",
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        logo_inner.add_widget(logo_label)
        logo_card.add_widget(logo_inner)
        center_box.add_widget(logo_card)

        # App name
        title = MDLabel(
            text="Flora Platform",
            font_style="Display",
            role="small",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )
        center_box.add_widget(title)

        # Tagline
        tagline = MDLabel(
            text="Seu chatbot WhatsApp, simplificado",
            font_style="Title",
            role="small",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
        )
        center_box.add_widget(tagline)

        layout.add_widget(center_box)

        # Loading indicator at bottom
        from kivymd.uix.progressindicator import MDLinearProgressIndicator
        self.loader = MDLinearProgressIndicator(
            size_hint_x=0.5,
            pos_hint={"center_x": 0.5, "y": 0.05},
            indicator_color=(1.0, 0.420, 0.616, 1),
        )
        layout.add_widget(self.loader)

        self.add_widget(layout)

    def on_enter(self):
        """Animate in when screen is shown."""
        # Fade in animation
        anim = Animation(opacity_val=1, duration=0.8)
        anim.start(self)
        # Start loading animation
        Clock.schedule_interval(self._animate_loader, 0.05)
        # Navigate after 2.5 seconds
        Clock.schedule_once(self._go_next, 2.5)

    def _animate_loader(self, dt):
        if self.loader.value is None:
            self.loader.value = 0
        self.loader.value = (self.loader.value + 2) % 100
        return True

    def _go_next(self, dt):
        """Navigate to the next screen."""
        # Stop the loader animation
        Clock.unschedule(self._animate_loader)
        # Check if user has already seen welcome screen
        from apps.client.main import get_stored_token, load_token_data
        token = get_stored_token()
        data = load_token_data()
        seen_welcome = data.get("seen_welcome", False) if data else False

        if token:
            self.manager.current = "dashboard"
        elif seen_welcome:
            self.manager.current = "license"
        else:
            self.manager.current = "welcome"

    def on_leave(self):
        Clock.unschedule(self._animate_loader)
