# ═══════════════════════════════════════════════════════════════
# Flora Platform — Tela de Licenças
# ═══════════════════════════════════════════════════════════════

from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.scrollview import ScrollView

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import (
    MDRaisedButton, MDIconButton, MDFlatButton, MDFloatingActionButton
)
from kivymd.uix.card import MDCard
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.textfield import MDTextField
from kivymd.uix.chip import MDChip
from kivymd.uix.dialog import MDDialog
from kivymd.toast import toast

from apps.shared.api_client import api


class LicensesScreen(Screen):
    """Tela de gerenciamento de licenças."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "licenses"
        self._dialog = None
        self._loading = False
        self._licenses = []
        self._build()
        Clock.schedule_once(lambda dt: self._load_licenses(), 0.5)

    def _build(self):
        """Constrói a tela de licenças."""
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

        title = MDLabel(
            text="Licenças",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6",
            bold=True,
        )

        spacer = MDBoxLayout(size_hint_x=1)

        search_btn = MDIconButton(
            icon="magnify",
            theme_icon_color="Custom",
            icon_color=(0.69, 0.745, 0.773, 1),
            on_release=self._toggle_search,
        )

        refresh_btn = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color=(0.424, 0.388, 1.0, 1),
            on_release=lambda x: self._load_licenses(),
        )

        toolbar.add_widget(back_btn)
        toolbar.add_widget(title)
        toolbar.add_widget(spacer)
        toolbar.add_widget(search_btn)
        toolbar.add_widget(refresh_btn)
        main_layout.add_widget(toolbar)

        # ── Barra de Pesquisa ───────────────────────────────────
        self.search_box = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(0),
            opacity=0,
            padding=[dp(16), dp(0)],
        )

        self.search_field = MDTextField(
            hint_text="Buscar licenças...",
            mode="round",
            radius=[dp(10)],
            size_hint_x=0.8,
            height=dp(48),
            hint_text_color_normal=(0.376, 0.49, 0.545, 1),
            text_color_normal=(1, 1, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            line_color_normal=(0.227, 0.294, 0.431, 1),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            fill_color_normal=(0.055, 0.106, 0.243, 1),
        )

        search_go = MDIconButton(
            icon="magnify",
            theme_icon_color="Custom",
            icon_color=(0.424, 0.388, 1.0, 1),
            on_release=lambda x: self._load_licenses(search=self.search_field.text),
        )

        self.search_box.add_widget(self.search_field)
        self.search_box.add_widget(search_go)
        main_layout.add_widget(self.search_box)

        # ── Filtros ─────────────────────────────────────────────
        filters = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            padding=[dp(16), dp(0)],
            spacing=dp(8),
        )

        for label_text, ftype in [("Todas", "all"), ("Ativas", "active"), ("Expiradas", "expired"), ("Revogadas", "revoked")]:
            chip = MDChip(
                text=label_text,
                icon="",
                selected=(ftype == "all"),
                md_bg_color=(0.424, 0.388, 1.0, 1) if ftype == "all" else (0, 0, 0, 0),
                text_color=(1, 1, 1, 1) if ftype == "all" else (0.69, 0.745, 0.773, 1),
                on_release=lambda x, ft=ftype: self._filter_licenses(ft),
            )
            filters.add_widget(chip)

        filters.add_widget(MDBoxLayout(size_hint_x=1))
        main_layout.add_widget(filters)

        # ── Lista de Licenças ───────────────────────────────────
        scroll = ScrollView()
        self.licenses_list = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(8)],
            spacing=dp(12),
            size_hint_y=None,
        )
        self.licenses_list.bind(minimum_height=self.licenses_list.setter("height"))

        self._loading_box = MDBoxLayout(size_hint_y=None, height=dp(200))
        self._spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            active=True,
        )
        self._loading_box.add_widget(self._spinner)
        self.licenses_list.add_widget(self._loading_box)

        scroll.add_widget(self.licenses_list)
        main_layout.add_widget(scroll)

        # ── FAB ─────────────────────────────────────────────────
        fab_box = MDBoxLayout(size_hint_y=None, height=dp(80))
        fab = MDFloatingActionButton(
            icon="plus",
            pos_hint={"center_x": 0.92, "center_y": 0.5},
            md_bg_color=(0.424, 0.388, 1.0, 1),
            icon_color=(1, 1, 1, 1),
            on_release=lambda x: self._go_to("license_form"),
        )
        fab_box.add_widget(fab)
        main_layout.add_widget(fab_box)

        self.add_widget(main_layout)

    def _toggle_search(self, *args):
        if self.search_box.height == 0:
            self.search_box.height = dp(56)
            self.search_box.opacity = 1
            self.search_box.padding = [dp(16), dp(8)]
        else:
            self.search_box.height = dp(0)
            self.search_box.opacity = 0
            self.search_box.padding = [dp(16), dp(0)]

    def _filter_licenses(self, filter_type):
        self._current_filter = filter_type
        self._render_licenses()

    def _load_licenses(self, search=None):
        if self._loading:
            return
        self._loading = True
        self._spinner.active = True
        self._loading_box.height = dp(200)
        self._loading_box.opacity = 1

        params = {}
        if search:
            params["search"] = search

        def _on_result(result):
            Clock.schedule_once(lambda dt: self._handle_licenses(result), 0)

        api.get_async("/admin/licenses", _on_result, params if params else None)

    def _handle_licenses(self, result):
        self._loading = False
        self._loading_box.height = dp(0)
        self._loading_box.opacity = 0
        self._spinner.active = False

        if result.get("error"):
            toast("Erro ao carregar licenças.")
            return

        self._licenses = result.get("licenses", [])
        self._render_licenses()

    def _render_licenses(self):
        self.licenses_list.clear_widgets()

        licenses = self._licenses
        filter_type = getattr(self, "_current_filter", "all")

        if filter_type != "all":
            licenses = [l for l in licenses if l.get("status") == filter_type]

        if not licenses:
            empty = MDBoxLayout(size_hint_y=None, height=dp(120))
            empty.add_widget(MDLabel(
                text="Nenhuma licença encontrada.",
                theme_text_color="Custom",
                text_color=(0.376, 0.49, 0.545, 1),
                font_style="Body1",
                halign="center",
            ))
            self.licenses_list.add_widget(empty)
            return

        for lic in licenses:
            card = self._create_license_card(lic)
            self.licenses_list.add_widget(card)

    def _create_license_card(self, lic):
        status = lic.get("status", "unknown")
        if status == "active":
            status_color = (0.302, 0.765, 0.314, 1)
            status_text = "Ativa"
        elif status == "expired":
            status_color = (0.957, 0.612, 0.0, 1)
            status_text = "Expirada"
        elif status == "revoked":
            status_color = (0.957, 0.263, 0.212, 1)
            status_text = "Revogada"
        else:
            status_color = (0.376, 0.49, 0.545, 1)
            status_text = status.capitalize()

        # Mascara a chave
        key = lic.get("license_key", "")
        if len(key) > 12:
            masked_key = key[:8] + "..." + key[-4:]
        else:
            masked_key = key

        card = MDCard(
            orientation="vertical",
            radius=[dp(16)],
            elevation=2,
            padding=dp(16),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(150),
            md_bg_color=(0.11, 0.165, 0.298, 1),
        )

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
        )

        key_lbl = MDLabel(
            text=masked_key,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6",
            bold=True,
            size_hint_x=0.7,
        )

        status_chip = MDChip(
            text=f"  {status_text}  ",
            icon="",
            md_bg_color=(*status_color[:3], 0.15),
            text_color=status_color,
            size_hint_x=None,
            width=dp(90),
            height=dp(28),
            font_size=dp(11),
        )

        header.add_widget(key_lbl)
        header.add_widget(status_chip)
        card.add_widget(header)

        # Info
        info = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(2),
        )

        expires = lic.get("expires_at", "N/A")
        if expires and len(str(expires)) > 10:
            expires = str(expires)[:10]

        info.add_widget(MDLabel(
            text=f"Usuário: {lic.get('user_id', 'N/A')[:8]}...",
            theme_text_color="Custom",
            text_color=(0.376, 0.49, 0.545, 1),
            font_style="Caption",
        ))
        info.add_widget(MDLabel(
            text=f"Expira: {expires}",
            theme_text_color="Custom",
            text_color=(0.376, 0.49, 0.545, 1),
            font_style="Caption",
        ))
        card.add_widget(info)

        # Ações
        actions = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(4),
        )

        renew_btn = MDFlatButton(
            text="Renovar",
            theme_text_color="Custom",
            text_color=(0.302, 0.765, 0.314, 1),
            font_style="Button",
            on_release=lambda x, l=lic: self._renew_license(l),
        )

        revoke_btn = MDFlatButton(
            text="Revogar",
            theme_text_color="Custom",
            text_color=(0.957, 0.263, 0.212, 1),
            font_style="Button",
            on_release=lambda x, l=lic: self._revoke_license(l),
        )

        actions.add_widget(renew_btn)
        actions.add_widget(revoke_btn)
        actions.add_widget(MDBoxLayout(size_hint_x=1))
        card.add_widget(actions)

        return card

    def _renew_license(self, lic):
        toast("Licença renovada!")

    def _revoke_license(self, lic):
        if self._dialog:
            self._dialog.dismiss()

        self._dialog = MDDialog(
            title="Revogar Licença",
            text="Tem certeza que deseja revogar esta licença?",
            buttons=[
                MDFlatButton(
                    text="Cancelar",
                    theme_text_color="Custom",
                    text_color=(0.69, 0.745, 0.773, 1),
                    on_release=lambda x: self._dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="Revogar",
                    md_bg_color=(0.957, 0.263, 0.212, 1),
                    text_color=(1, 1, 1, 1),
                    on_release=lambda x: self._do_revoke(lic),
                ),
            ],
        )
        self._dialog.open()

    def _do_revoke(self, lic):
        self._dialog.dismiss()
        toast("Licença revogada.")

    def _go_back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"

    def _go_to(self, screen):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen

    def on_enter(self, *args):
        Clock.schedule_once(lambda dt: self._load_licenses(), 0.3)
        return super().on_enter(*args)
