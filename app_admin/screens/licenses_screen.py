"""
Licenses Screen for the Flora Admin Panel.
License management: generate, revoke, activate, and view licenses.
"""
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.chip import MDChip

from app_admin.services.api_client import api_client
from app_admin.utils.constants import Colors, LICENSE_STATUS_LABELS
from app_admin.utils.helpers import format_datetime, get_status_color, generate_license_key


class LicenseListItem(MDCard):
    """A single license list item."""

    def __init__(self, license_data=None, **kwargs):
        super().__init__(
            orientation="horizontal",
            padding=dp(12),
            spacing=dp(12),
            md_bg_color=Colors.BG_SURFACE,
            radius=[dp(8)],
            elevation=dp(2),
            size_hint_y=None,
            height=dp(80),
            **kwargs,
        )
        self.license_data = license_data or {}
        self._build()

    def _build(self):
        data = self.license_data
        status = data.get("status", "pending")
        status_color = get_status_color(status, LICENSE_STATUS_LABELS)

        # Status indicator
        status_indicator = MDIconButton(
            icon="circle",
            icon_size=dp(12),
            theme_icon_color="Custom",
            icon_color=status_color,
            size_hint_x=None,
            width=dp(32),
            disabled=True,
        )
        self.add_widget(status_indicator)

        # Key icon
        key_icon = MDIconButton(
            icon="key-variant",
            icon_size=dp(24),
            theme_icon_color="Custom",
            icon_color=Colors.PRIMARY_LIGHT,
            size_hint_x=None,
            width=dp(40),
            disabled=True,
        )
        self.add_widget(key_icon)

        # Info
        info = MDBoxLayout(orientation="vertical", spacing=dp(2))

        key = data.get("key", "N/A")
        plan_name = data.get("plan_name", "N/A")
        name_label = MDLabel(
            text=f"[b]{key}[/b]  -  {plan_name}",
            markup=True,
            font_style="Body1",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            shorten=True,
            shorten_from="right",
        )
        info.add_widget(name_label)

        # Status chip and owner
        sub_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(24),
        )

        status_text = LICENSE_STATUS_LABELS.get(status, status)
        status_chip = MDChip(
            text=status_text,
            md_bg_color=(*status_color[:3], 0.2),
            text_color=status_color,
            icon="",
        )
        sub_row.add_widget(status_chip)

        owner = data.get("user_name", data.get("user_email", "N/A"))
        owner_label = MDLabel(
            text=f"Dono: {owner}",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
        )
        sub_row.add_widget(owner_label)

        expires = data.get("expires_at")
        if expires:
            exp_label = MDLabel(
                text=f"Expira: {format_datetime(expires)}",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
            )
            sub_row.add_widget(exp_label)

        info.add_widget(sub_row)
        self.add_widget(info)

        # Actions
        actions = MDBoxLayout(
            orientation="horizontal",
            size_hint_x=None,
            width=dp(96),
            spacing=dp(4),
        )

        view_btn = MDIconButton(
            icon="eye",
            theme_text_color="Custom",
            icon_color=Colors.INFO,
            on_release=lambda x: self._on_view(),
        )
        actions.add_widget(view_btn)

        if status == "active":
            action_btn = MDIconButton(
                icon="cancel",
                theme_icon_color="Custom",
                icon_color=Colors.ERROR,
                on_release=lambda x: self._on_revoke(),
            )
        else:
            action_btn = MDIconButton(
                icon="check-circle",
                theme_icon_color="Custom",
                icon_color=Colors.SUCCESS,
                on_release=lambda x: self._on_activate(),
            )
        actions.add_widget(action_btn)

        self.add_widget(actions)

    def _on_view(self):
        if self.parent and hasattr(self.parent, "parent") and hasattr(self.parent.parent, "show_license_details"):
            self.parent.parent.show_license_details(self.license_data)

    def _on_revoke(self):
        if self.parent and hasattr(self.parent, "parent") and hasattr(self.parent.parent, "revoke_license"):
            self.parent.parent.revoke_license(self.license_data)

    def _on_activate(self):
        if self.parent and hasattr(self.parent, "parent") and hasattr(self.parent.parent, "activate_license"):
            self.parent.parent.activate_license(self.license_data)


class LicensesScreen(MDScreen):
    """License management screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "licenses"
        self._licenses = []
        self._page = 1
        self._build_ui()

    def _build_ui(self):
        """Build the licenses screen UI."""
        main_layout = MDBoxLayout(
            orientation="vertical",
            md_bg_color=Colors.BG_DARK,
        )

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            padding=[dp(16), dp(8)],
            spacing=dp(8),
            md_bg_color=Colors.BG_CARD,
        )

        menu_btn = MDIconButton(
            icon="menu",
            theme_icon_color="Custom",
            icon_color=Colors.TEXT_PRIMARY,
            on_release=self._open_drawer,
        )
        header.add_widget(menu_btn)

        header_title = MDLabel(
            text="Gerenciar Licencas",
            font_style="H6",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            bold=True,
        )
        header.add_widget(header_title)

        header.add_widget(MDBoxLayout())

        gen_btn = MDRaisedButton(
            text="Gerar Licenca",
            icon="plus",
            md_bg_color=Colors.SUCCESS,
            text_color=Colors.TEXT_PRIMARY,
            on_release=self._generate_license,
        )
        header.add_widget(gen_btn)

        refresh_btn = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color=Colors.TEXT_SECONDARY,
            on_release=self._load_licenses,
        )
        header.add_widget(refresh_btn)

        main_layout.add_widget(header)

        # Search bar
        search_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(16), dp(4)],
            spacing=dp(8),
            md_bg_color=Colors.BG_DARK,
        )

        self.search_field = MDTextField(
            hint_text="Buscar por chave ou usuario...",
            mode="round",
            icon_left="magnify",
            text="",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            icon_color_normal=Colors.TEXT_SECONDARY,
            icon_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(12)],
            size_hint_x=0.7,
            on_text_validate=self._on_search,
        )
        search_bar.add_widget(self.search_field)

        # Status filter chips
        self.chip_all = MDChip(
            text="Todas",
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.TEXT_PRIMARY,
            icon="",
            on_release=lambda x: self._filter_status(""),
        )
        search_bar.add_widget(self.chip_all)

        self.chip_active = MDChip(
            text="Ativas",
            md_bg_color=Colors.BG_SURFACE,
            text_color=Colors.TEXT_SECONDARY,
            icon="",
            on_release=lambda x: self._filter_status("active"),
        )
        search_bar.add_widget(self.chip_active)

        self.chip_expired = MDChip(
            text="Expiradas",
            md_bg_color=Colors.BG_SURFACE,
            text_color=Colors.TEXT_SECONDARY,
            icon="",
            on_release=lambda x: self._filter_status("expired"),
        )
        search_bar.add_widget(self.chip_expired)

        main_layout.add_widget(search_bar)

        # Licenses list
        self.licenses_list = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(8)],
            spacing=dp(8),
            size_hint_y=None,
        )
        self.licenses_list.bind(minimum_height=self.licenses_list.setter("height"))

        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(4))
        scroll.add_widget(self.licenses_list)
        main_layout.add_widget(scroll)

        # Loading
        self.loading_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(0),
            padding=dp(16),
        )
        self.loading_spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            active=False,
            color=Colors.PRIMARY_LIGHT,
            pos_hint={"center_x": 0.5},
        )
        self.loading_box.add_widget(self.loading_spinner)
        main_layout.add_widget(self.loading_box)

        # Pagination
        pagination = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            padding=[dp(16), dp(4)],
            spacing=dp(8),
            md_bg_color=Colors.BG_CARD,
        )

        self.prev_btn = MDRaisedButton(
            text="Anterior",
            md_bg_color=Colors.BG_SURFACE,
            text_color=Colors.TEXT_PRIMARY,
            on_release=self._prev_page,
        )
        pagination.add_widget(self.prev_btn)

        self.page_label = MDLabel(
            text="Pagina 1",
            halign="center",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
        )
        pagination.add_widget(self.page_label)

        self.next_btn = MDRaisedButton(
            text="Proxima",
            md_bg_color=Colors.BG_SURFACE,
            text_color=Colors.TEXT_PRIMARY,
            on_release=self._next_page,
        )
        pagination.add_widget(self.next_btn)

        main_layout.add_widget(pagination)

        self.add_widget(main_layout)
        self._current_status_filter = ""

    def _open_drawer(self, *args):
        nav_drawer = self.manager.parent.ids.get("nav_drawer") if hasattr(self.manager.parent, "ids") else None
        if nav_drawer:
            nav_drawer.set_state("open")

    def on_pre_enter(self):
        self._load_licenses()

    def _load_licenses(self, *args):
        """Load licenses from API."""
        self.loading_box.height = dp(60)
        self.loading_spinner.active = True
        self.licenses_list.clear_widgets()

        def _on_data(result, error):
            self.loading_box.height = dp(0)
            self.loading_spinner.active = False

            if error:
                self._show_placeholder(f"Erro: {error.message}")
                return

            if result:
                licenses = result.get("licenses", result.get("items", []))
                self._licenses = licenses
                self._update_list()

        search = self.search_field.text.strip()
        api_client.get_licenses_async(
            _on_data,
            page=self._page,
            search=search,
            status=self._current_status_filter,
        )

    def _update_list(self):
        """Update the licenses list display."""
        self.licenses_list.clear_widgets()

        if not self._licenses:
            self._show_placeholder("Nenhuma licenca encontrada")
            return

        for lic in self._licenses:
            item = LicenseListItem(license_data=lic)
            self.licenses_list.add_widget(item)

        self.page_label.text = f"Pagina {self._page}"

    def _show_placeholder(self, text):
        label = MDLabel(
            text=text,
            halign="center",
            font_style="Body1",
            theme_text_color="Custom",
            text_color=Colors.TEXT_HINT,
            size_hint_y=None,
            height=dp(60),
        )
        self.licenses_list.add_widget(label)

    def _on_search(self, *args):
        self._page = 1
        self._load_licenses()

    def _filter_status(self, status):
        self._current_status_filter = status
        self._page = 1
        self._load_licenses()

    def _prev_page(self, *args):
        if self._page > 1:
            self._page -= 1
            self._load_licenses()

    def _next_page(self, *args):
        self._page += 1
        self._load_licenses()

    def _generate_license(self, *args):
        """Open dialog to generate a new license."""
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(200),
            padding=dp(8),
        )

        # Plan selection
        plan_field = MDTextField(
            hint_text="ID do Plano",
            mode="round",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(8)],
        )
        content.add_widget(plan_field)

        # User email
        user_field = MDTextField(
            hint_text="Email do usuario (opcional)",
            mode="round",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(8)],
        )
        content.add_widget(user_field)

        # Trial toggle
        trial_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
            spacing=dp(8),
        )
        trial_row.add_widget(MDLabel(
            text="Licenca de teste",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        ))
        trial_row.add_widget(MDBoxLayout())
        trial_switch = MDSwitch(active=False, pos_hint={"center_y": 0.5})
        trial_row.add_widget(trial_switch)
        content.add_widget(trial_row)

        def _do_generate(*args):
            data = {
                "plan_id": plan_field.text.strip(),
                "is_trial": trial_switch.active,
            }
            user_email = user_field.text.strip()
            if user_email:
                data["user_email"] = user_email

            if not data["plan_id"]:
                return

            api_client.generate_license(data)
            dialog.dismiss()
            Clock.schedule_once(lambda dt: self._load_licenses(), 0.5)

        dialog = MDDialog(
            title="Gerar Nova Licenca",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCELAR",
                    theme_text_color="Custom",
                    text_color=Colors.TEXT_SECONDARY,
                    on_release=lambda x: dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="GERAR",
                    md_bg_color=Colors.SUCCESS,
                    text_color=Colors.TEXT_PRIMARY,
                    on_release=_do_generate,
                ),
            ],
        )
        dialog.open()

    def show_license_details(self, license_data):
        """Show license details in a dialog."""
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(380),
            padding=dp(8),
        )

        status = license_data.get("status", "pending")
        status_color = get_status_color(status, LICENSE_STATUS_LABELS)

        fields = [
            ("Chave", license_data.get("key", "N/A")),
            ("Status", LICENSE_STATUS_LABELS.get(status, status)),
            ("Plano", license_data.get("plan_name", "N/A")),
            ("Dono", license_data.get("user_name", license_data.get("user_email", "N/A"))),
            ("Dispositivo", license_data.get("device_name", "N/A")),
            ("Max dispositivos", str(license_data.get("max_devices", 1))),
            ("Dispositivos ativos", str(license_data.get("current_devices", 0))),
            ("Teste", "Sim" if license_data.get("is_trial") else "Nao"),
            ("Criada em", format_datetime(license_data.get("created_at"))),
            ("Ativada em", format_datetime(license_data.get("activated_at"))),
            ("Expira em", format_datetime(license_data.get("expires_at"))),
        ]

        for label, value in fields:
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(30),
                spacing=dp(8),
            )
            row.add_widget(MDLabel(
                text=f"[b]{label}:[/b]",
                markup=True,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
                size_hint_x=0.4,
            ))
            row.add_widget(MDLabel(
                text=str(value),
                font_style="Caption",
                theme_text_color="Custom",
                text_color=Colors.TEXT_PRIMARY,
                size_hint_x=0.6,
                shorten=True,
            ))
            content.add_widget(row)

        self.dialog = MDDialog(
            title="Detalhes da Licenca",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="FECHAR",
                    theme_text_color="Custom",
                    text_color=Colors.PRIMARY_LIGHT,
                    on_release=lambda x: self.dialog.dismiss(),
                ),
            ],
        )
        self.dialog.open()

    def revoke_license(self, license_data):
        """Confirm and revoke a license."""
        lic_id = license_data.get("id", "")
        lic_key = license_data.get("key", "")

        def _confirm_revoke(*args):
            api_client.revoke_license(lic_id, reason="Revogada pelo administrador")
            confirm_dialog.dismiss()
            Clock.schedule_once(lambda dt: self._load_licenses(), 0.5)

        confirm_dialog = MDDialog(
            title="Revogar Licenca",
            text=f"Tem certeza que deseja revogar a licenca '{lic_key}'?",
            buttons=[
                MDFlatButton(
                    text="CANCELAR",
                    theme_text_color="Custom",
                    text_color=Colors.TEXT_SECONDARY,
                    on_release=lambda x: confirm_dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="REVOgar",
                    md_bg_color=Colors.ERROR,
                    text_color=Colors.TEXT_PRIMARY,
                    on_release=_confirm_revoke,
                ),
            ],
        )
        confirm_dialog.open()

    def activate_license(self, license_data):
        """Activate a license."""
        lic_id = license_data.get("id", "")
        api_client.activate_license(lic_id)
        Clock.schedule_once(lambda dt: self._load_licenses(), 0.5)
