# ═══════════════════════════════════════════════════════════════
# Flora Platform — License Screen
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
from kivymd.uix.progressindicator import MDCircularProgressIndicator


class LicenseScreen(MDScreen):
    """License key input and validation screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        self.md_bg_color = (0.102, 0.102, 0.180, 1)

        layout = MDFloatLayout()

        # Back button
        back_btn = MDButton(
            MDButtonText(text="", theme_text_color="Custom", text_color=(0.7, 0.7, 0.75, 1)),
            style="text",
            pos_hint={"x": 0.02, "top": 0.98},
        )
        layout.add_widget(back_btn)

        # Main card
        card = MDCard(
            orientation="vertical",
            size_hint=(0.88, 0.72),
            pos_hint={"center_x": 0.5, "center_y": 0.48},
            radius=[dp(28)],
            md_bg_color=(0.13, 0.16, 0.28, 1),
            padding=[dp(28), dp(24)],
            spacing=dp(20),
            elevation=6,
        )

        # Icon
        icon_label = MDLabel(
            text="🔑",
            font_size=sp(56),
            halign="center",
            size_hint_y=None,
            height=dp(70),
        )
        card.add_widget(icon_label)

        # Title
        title = MDLabel(
            text="Ative sua Licenca",
            font_style="Headline",
            role="small",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(40),
        )
        card.add_widget(title)

        # Description
        desc = MDLabel(
            text="Insira a chave de licenca que voce recebeu por email ou no seu painel de compra.",
            font_style="Body",
            role="medium",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.75, 1),
            size_hint_y=None,
            adaptive_height=True,
        )
        card.add_widget(desc)

        # Spacer
        card.add_widget(MDBoxLayout(size_hint_y=None, height=dp(10)))

        # License key input
        self.license_input = MDTextField(
            mode="outlined",
            size_hint_y=None,
            height=dp(56),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            line_color_normal=(0.3, 0.3, 0.4, 1),
            hint_text="XXXX-XXXX-XXXX-XXXX",
            helper_text="Formato: XXXX-XXXX-XXXX-XXXX",
            helper_text_mode="on_focus",
            text_color_normal=(0.7, 0.7, 0.75, 1),
            text_color_focus=(1, 1, 1, 1),
            fill_color_normal=(0.13, 0.16, 0.28, 1),
        )
        card.add_widget(self.license_input)

        # Error label
        self.error_label = MDLabel(
            text="",
            font_style="Label",
            role="large",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.957, 0.263, 0.212, 1),
            size_hint_y=None,
            height=dp(20),
        )
        card.add_widget(self.error_label)

        # Spacer
        card.add_widget(MDBoxLayout(size_hint_y=None, height=dp(4)))

        # Validate button
        self.validate_btn = MDButton(
            MDButtonText(text="Validar Licenca"),
            style="filled",
            size_hint=(1, None),
            height=dp(52),
            radius=[dp(16)],
            md_bg_color=(0.424, 0.388, 1.0, 1),
            on_release=self._on_validate,
        )
        card.add_widget(self.validate_btn)

        # Loading indicator (hidden initially)
        self.loader_box = MDBoxLayout(
            size_hint=(1, None),
            height=dp(52),
            opacity=0,
        )
        self.loader = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            pos_hint={"center_x": 0.5},
            indicator_color=(0.424, 0.388, 1.0, 1),
        )
        self.loader_box.add_widget(self.loader)
        card.add_widget(self.loader_box)

        layout.add_widget(card)

        # Help link at bottom
        help_btn = MDButton(
            MDButtonText(
                text="Onde encontrar minha licenca?",
                theme_text_color="Custom",
                text_color=(1.0, 0.420, 0.616, 1),
            ),
            style="text",
            pos_hint={"center_x": 0.5, "y": 0.04},
            on_release=self._on_help,
        )
        layout.add_widget(help_btn)

        self.add_widget(layout)

    def _on_validate(self, instance):
        """Validate the license key."""
        key = self.license_input.text.strip()
        if not key:
            self.error_label.text = "Por favor, insira sua chave de licenca."
            return

        # Show loading
        self.validate_btn.opacity = 0
        self.loader_box.opacity = 1
        self.error_label.text = ""
        self.loader.start()

        # Make async request
        from apps.client.main import api_request_async
        api_request_async(
            "POST",
            "/licenses/validate",
            data={"license_key": key, "device_fingerprint": "client-app"},
            callback=self._on_validation_result,
        )

    def _on_validation_result(self, result):
        """Handle validation result."""
        self.loader.stop()
        self.loader_box.opacity = 0
        self.validate_btn.opacity = 1

        if result["success"] and result["data"].get("valid"):
            data = result["data"]
            # Save token info (we'll get a real token after login)
            from apps.client.main import save_token_data
            save_token_data({
                "license_key": self.license_input.text.strip(),
                "license_valid": True,
                "license_data": data,
                "seen_welcome": True,
            })

            app = self.manager.parent if hasattr(self.manager, "parent") else None
            if app and hasattr(app, "show_snackbar"):
                app.show_snackbar("Licenca validada com sucesso!", (0.298, 0.686, 0.314, 1))

            # Check if user needs onboarding
            self.manager.current = "onboarding"
        else:
            reason = result.get("error", "Chave invalida ou expirada.")
            if isinstance(reason, str):
                self.error_label.text = reason
            else:
                self.error_label.text = "Chave invalida ou expirada."

    def _on_help(self, instance):
        """Show help dialog about finding license key."""
        from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Onde encontrar sua licenca?"),
            MDDialogSupportingText(
                text="Voce recebe sua chave de licenca por email apos a compra. "
                     "Verifique sua caixa de entrada e spam. Se comprou pelo site, "
                     "acesse 'Minhas Licencas' na sua conta."
            ),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Entendi"),
                    style="text",
                    on_release=lambda x: self.dialog.dismiss(),
                ),
                spacing=dp(8),
            ),
        )
        self.dialog.open()
