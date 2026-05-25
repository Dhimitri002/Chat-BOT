"""
Flora Platform — Splash Screen
=================================
Animated splash screen with logo, loading indicator,
and auto-navigation to login or home based on auth state.
"""
import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import Screen, FadeTransition
from kivy.lang import Builder

Builder.load_string(
    """
<SplashScreen>:
    name: "splash"
    canvas.before:
        Color:
            rgba: 0.102, 0.102, 0.18, 1
        Rectangle:
            pos: self.pos
            size: self.size

    FloatLayout:
        # Gradient-like overlay
        Image:
            source: ""
            allow_stretch: True
            keep_ratio: False
            color: 0.102, 0.102, 0.18, 1
            pos_hint: {"center_x": 0.5, "center_y": 0.5}

        # Top decorative bar
        BoxLayout:
            pos_hint: {"center_x": 0.5, "top": 1}
            size_hint: 1, 0.004
            canvas.before:
                Color:
                    rgba: 0.914, 0.271, 0.376, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

        # Logo area
        FloatLayout:
            size_hint: 1, 0.6
            pos_hint: {"center_x": 0.5, "center_y": 0.55}

            # Flora emoji logo
            Label:
                text: ""
                font_size: "120sp"
                pos_hint: {"center_x": 0.5, "center_y": 0.65}
                opacity: root.logo_opacity

            # App name
            Label:
                text: "Flora"
                font_size: "52sp"
                bold: True
                color: 1, 1, 1, 1
                pos_hint: {"center_x": 0.5, "center_y": 0.38}
                opacity: root.logo_opacity

            # Tagline
            Label:
                text: "WhatsApp Chatbot Platform"
                font_size: "16sp"
                color: 0.914, 0.271, 0.376, 0.8
                pos_hint: {"center_x": 0.5, "center_y": 0.30}
                opacity: root.logo_opacity

        # Bottom section
        BoxLayout:
            orientation: "vertical"
            size_hint: 1, 0.2
            pos_hint: {"center_x": 0.5, "y": 0}
            padding: dp(40)
            spacing: dp(16)

            # Loading bar outer
            BoxLayout:
                size_hint_y: None
                height: dp(4)
                pos_hint: {"center_x": 0.5}
                canvas.before:
                    Color:
                        rgba: 0.137, 0.129, 0.243, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(2)]

                # Loading bar inner
                BoxLayout:
                    size_hint_x: root.loading_progress
                    canvas.before:
                        Color:
                            rgba: 0.914, 0.271, 0.376, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(2)]

            # Version
            Label:
                text: "v1.0.0"
                font_size: "11sp"
                color: 0.4, 0.4, 0.5, 1
                size_hint_y: None
                height: dp(20)
"""
)


class SplashScreen(Screen):
    """Animated splash screen with logo and loading animation."""

    logo_opacity = NumericProperty(0)
    loading_progress = NumericProperty(0)

    def on_enter(self):
        """Start splash animation when screen is shown."""
        self.logo_opacity = 0
        self.loading_progress = 0
        self._start_animation()

    def _start_animation(self):
        """Animate logo fade-in and loading bar."""
        # Fade in logo
        anim = Animation(logo_opacity=1, duration=0.8)
        anim.start(self)

        # Animate loading bar
        Clock.schedule_once(lambda dt: self._animate_loading(), 0.5)

    def _animate_loading(self):
        """Animate the loading progress bar."""
        anim = Animation(loading_progress=1, duration=2.0)
        anim.bind(on_complete=self._on_loading_complete)
        anim.start(self)

    def _on_loading_complete(self, *args):
        """Navigate after loading completes."""
        Clock.schedule_once(lambda dt: self._check_auth_and_navigate(), 0.3)

    def _check_auth_and_navigate(self):
        """Check auth state and navigate accordingly."""
        app = App.get_running_app()
        try:
            auth = app.auth_service
            if auth and auth.is_authenticated:
                # Try to validate the session
                if auth.check_auth():
                    self.manager.current = "home"
                    return
        except Exception:
            pass
        self.manager.current = "login"
