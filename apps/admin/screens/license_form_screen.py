# ═══════════════════════════════════════════════════════════════
# Flora Platform — Formulário de Licença
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
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.toast import toast

from apps.shared.api_client import api


class LicenseFormScreen(Screen):
    """Tela de criação/edição de licença."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "license_form"
        self._license_id = None
        self._users = []
        self._plans = []
        self._build()
        Clock.schedule_once(lambda dt: self._load_options(), 0.3)

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
            text="Nova Licença",
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

        # Seleção de Usuário
        form_card.add_widget(MDLabel(
            text="Usuário *",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        ))
        self.user_field = MDTextField(
            hint_text="Selecione um usuário",
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
            icon_right="chevron-down",
            readonly=True,
        )
        self.user_field.bind(on_release=self._show_user_picker)
        form_card.add_widget(self.user_field)

        # Seleção de Plano
        form_card.add_widget(MDLabel(
            text="Plano *",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        ))
        self.plan_field = MDTextField(
            hint_text="Selecione um plano",
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
            icon_right="chevron-down",
            readonly=True,
        )
        self.plan_field.bind(on_release=self._show_plan_picker)
        form_card.add_widget(self.plan_field)

        # Duração (dias)
        form_card.add_widget(MDLabel(
            text="Duração (dias) *",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        ))
        self.duration_field = MDTextField(
            hint_text="30",
            mode="round",
            radius=[dp(10)],
            size_hint_y=None,
            height=dp(52),
            text="30",
            hint_text_color_normal=(0.376, 0.49, 0.545, 1),
            text_color_normal=(1, 1, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            line_color_normal=(0.227, 0.294, 0.431, 1),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            fill_color_normal=(0.055, 0.106, 0.243, 1),
            input_filter="int",
        )
        form_card.add_widget(self.duration_field)

        # Auto-renovação
        auto_renew_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
        )

        self.auto_renew_checkbox = MDCheckbox(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={"center_y": 0.5},
            color=(0.424, 0.388, 1.0, 1),
        )

        auto_renew_lbl = MDLabel(
            text="Renovação automática",
            theme_text_color="Custom",
            text_color=(0.69, 0.745, 0.773, 1),
            font_style="Body2",
        )

        auto_renew_row.add_widget(self.auto_renew_checkbox)
        auto_renew_row.add_widget(auto_renew_lbl)
        auto_renew_row.add_widget(MDBoxLayout(size_hint_x=1))
        form_card.add_widget(auto_renew_row)

        # Gerar Chave
        gen_key_btn = MDFlatButton(
            text="Gerar Chave de Licença",
            theme_text_color="Custom",
            text_color=(0.424, 0.388, 1.0, 1),
            font_style="Button",
            on_release=self._generate_key,
        )
        form_card.add_widget(gen_key_btn)

        # Chave gerada
        self.key_field = MDTextField(
            hint_text="Chave será gerada...",
            mode="round",
            radius=[dp(10)],
            readonly=True,
            size_hint_y=None,
            height=dp(52),
            hint_text_color_normal=(0.376, 0.49, 0.545, 1),
            text_color_normal=(1, 1, 1, 1),
            line_color_normal=(0.227, 0.294, 0.431, 1),
            line_color_focus=(0.424, 0.388, 1.0, 1),
            fill_color_normal=(0.055, 0.106, 0.243, 1),
        )
        form_card.add_widget(self.key_field)

        form.add_widget(form_card)

        # ── Botões ──────────────────────────────────────────────
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

    def _load_options(self):
        """Carrega usuários e planos para seleção."""
        def _on_users(result):
            if not result.get("error"):
                self._users = result.get("users", [])

        def _on_plans(result):
            if not result.get("error"):
                self._plans = result.get("plans", [])

        api.get_async("/admin/users", _on_users)
        api.get_async("/plans", _on_plans)

    def _show_user_picker(self, *args):
        """Mostra diálogo de seleção de usuário."""
        if not self._users:
            toast("Nenhum usuário disponível.")
            return

        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.list import OneLineListItem, MDList
        from kivy.uix.scrollview import ScrollView

        sv = ScrollView()
        lst = MDList()
        for u in self._users[:20]:
            item = OneLineListItem(
                text=f"{u.get('name', 'Sem nome')} ({u.get('email', '')})",
                on_release=lambda x, user=u: self._select_user(user),
            )
            lst.add_widget(item)
        sv.add_widget(lst)

        self._picker = MDDialog(
            title="Selecionar Usuário",
            type="custom",
            content_cls=sv,
            buttons=[
                MDFlatButton(
                    text="Fechar",
                    theme_text_color="Custom",
                    text_color=(0.69, 0.745, 0.773, 1),
                    on_release=lambda x: self._picker.dismiss(),
                ),
            ],
        )
        self._picker.open()

    def _select_user(self, user):
        self._selected_user = user
        self.user_field.text = f"{user.get('name', 'Sem nome')} ({user.get('email', '')})"
        if hasattr(self, '_picker'):
            self._picker.dismiss()

    def _show_plan_picker(self, *args):
        if not self._plans:
            toast("Nenhum plano disponível.")
            return

        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.list import OneLineListItem, MDList
        from kivy.uix.scrollview import ScrollView

        sv = ScrollView()
        lst = MDList()
        for p in self._plans:
            item = OneLineListItem(
                text=f"{p.get('name', 'Sem nome')} - R${p.get('price_monthly', 0):.2f}/mês",
                on_release=lambda x, plan=p: self._select_plan(plan),
            )
            lst.add_widget(item)
        sv.add_widget(lst)

        self._picker = MDDialog(
            title="Selecionar Plano",
            type="custom",
            content_cls=sv,
            buttons=[
                MDFlatButton(
                    text="Fechar",
                    theme_text_color="Custom",
                    text_color=(0.69, 0.745, 0.773, 1),
                    on_release=lambda x: self._picker.dismiss(),
                ),
            ],
        )
        self._picker.open()

    def _select_plan(self, plan):
        self._selected_plan = plan
        self.plan_field.text = f"{plan.get('name', 'Sem nome')} - R${plan.get('price_monthly', 0):.2f}/mês"
        if hasattr(self, '_picker'):
            self._picker.dismiss()

    def _generate_key(self, *args):
        """Gera uma chave de licença aleatória."""
        import uuid
        key = f"FLORA-{uuid.uuid4().hex[:8].upper()}-{uuid.uuid4().hex[:8].upper()}"
        self.key_field.text = key

    def _save(self):
        """Salva a licença."""
        if not hasattr(self, '_selected_user') or not self._selected_user:
            toast("Selecione um usuário.")
            return
        if not hasattr(self, '_selected_plan') or not self._selected_plan:
            toast("Selecione um plano.")
            return

        try:
            days = int(self.duration_field.text.strip())
        except ValueError:
            days = 30

        data = {
            "user_id": self._selected_user.get("id"),
            "plan_id": self._selected_plan.get("id"),
            "days_valid": days,
        }

        self.save_btn.opacity = 0
        self.save_btn.disabled = True
        self._save_spinner.active = True

        def _on_result(result):
            Clock.schedule_once(lambda dt: self._handle_save(result), 0)

        api.post_async("/admin/licenses", _on_result, data)

    def _handle_save(self, result):
        self.save_btn.opacity = 1
        self.save_btn.disabled = False
        self._save_spinner.active = False

        if result.get("error"):
            toast(result.get("message", "Erro ao salvar licença."))
        else:
            toast("Licença criada com sucesso!")
            self._go_back()

    def _go_back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "licenses"

    def on_leave(self, *args):
        self._license_id = None
        self._selected_user = None
        self._selected_plan = None
        self.user_field.text = ""
        self.plan_field.text = ""
        self.duration_field.text = "30"
        self.key_field.text = ""
        self.auto_renew_checkbox.active = False
        return super().on_leave(*args)
