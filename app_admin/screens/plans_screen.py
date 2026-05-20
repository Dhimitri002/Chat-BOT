"""
Plans Screen for the Flora Admin Panel.
Plan management: create, edit, delete plans with pricing and features.
"""
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.checkbox import MDCheckbox
from kivymd.uix.switch import MDSwitch

from app_admin.services.api_client import api_client
from app_admin.utils.constants import Colors
from app_admin.utils.helpers import format_currency


class PlanCard(MDCard):
    """A card displaying a plan."""

    def __init__(self, plan_data=None, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            md_bg_color=Colors.BG_CARD,
            radius=[dp(12)],
            elevation=dp(4),
            size_hint_y=None,
            height=dp(220),
            **kwargs,
        )
        self.plan_data = plan_data or {}
        self._build()

    def _build(self):
        data = self.plan_data

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
        )

        name = data.get("name", "Plano")
        name_label = MDLabel(
            text=f"[b]{name}[/b]",
            markup=True,
            font_style="H6",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        )
        header.add_widget(name_label)
        header.add_widget(MDBoxLayout())

        # Edit and delete buttons
        edit_btn = MDIconButton(
            icon="pencil",
            theme_icon_color="Custom",
            icon_color=Colors.INFO,
            on_release=lambda x: self._on_edit(),
        )
        header.add_widget(edit_btn)

        delete_btn = MDIconButton(
            icon="delete",
            theme_icon_color="Custom",
            icon_color=Colors.ERROR,
            on_release=lambda x: self._on_delete(),
        )
        header.add_widget(delete_btn)

        self.add_widget(header)

        # Price
        price = data.get("price_monthly", 0)
        price_label = MDLabel(
            text=f"{format_currency(price)}/mes",
            font_style="H5",
            theme_text_color="Custom",
            text_color=Colors.PRIMARY_LIGHT,
            bold=True,
            size_hint_y=None,
            height=dp(32),
        )
        self.add_widget(price_label)

        # Description
        desc = data.get("description", "")
        if desc:
            desc_label = MDLabel(
                text=desc,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=Colors.TEXT_SECONDARY,
                size_hint_y=None,
                height=dp(20),
                shorten=True,
            )
            self.add_widget(desc_label)

        # Features summary
        features = MDBoxLayout(
            orientation="vertical",
            spacing=dp(2),
            size_hint_y=None,
            height=dp(80),
        )

        max_bots = data.get("max_bots", 0)
        max_msgs = data.get("max_messages_per_month", 0)
        max_intents = data.get("max_intents", 0)
        has_llm = data.get("has_llm", False)
        has_flora = data.get("has_flora_ai", False)

        feature_texts = [
            f"Ate {max_bots} bot(s)",
            f"{max_msgs:,} mensagens/mes".replace(",", "."),
            f"{max_intents} intencoes",
            f"{'Com LLM' if has_llm else 'Sem LLM'}",
            f"{'Com Flora AI' if has_flora else 'Sem Flora AI'}",
        ]

        for ft in feature_texts:
            lbl = MDLabel(
                text=f"- {ft}",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                size_hint_y=None,
                height=dp(16),
            )
            features.add_widget(lbl)

        self.add_widget(features)

    def _on_edit(self):
        if self.parent and hasattr(self.parent, "parent") and hasattr(self.parent.parent, "edit_plan"):
            self.parent.parent.edit_plan(self.plan_data)

    def _on_delete(self):
        if self.parent and hasattr(self.parent, "parent") and hasattr(self.parent.parent, "delete_plan"):
            self.parent.parent.delete_plan(self.plan_data)


class PlansScreen(MDScreen):
    """Plan management screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "plans"
        self._plans = []
        self._build_ui()

    def _build_ui(self):
        """Build the plans screen UI."""
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
            text="Gerenciar Planos",
            font_style="H6",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            bold=True,
        )
        header.add_widget(header_title)

        header.add_widget(MDBoxLayout())

        add_btn = MDRaisedButton(
            text="Novo Plano",
            icon="plus",
            md_bg_color=Colors.SUCCESS,
            text_color=Colors.TEXT_PRIMARY,
            on_release=self._create_plan,
        )
        header.add_widget(add_btn)

        refresh_btn = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color=Colors.TEXT_SECONDARY,
            on_release=self._load_plans,
        )
        header.add_widget(refresh_btn)

        main_layout.add_widget(header)

        # Plans grid
        self.plans_list = MDBoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12),
            size_hint_y=None,
        )
        self.plans_list.bind(minimum_height=self.plans_list.setter("height"))

        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(4))
        scroll.add_widget(self.plans_list)
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

        self.add_widget(main_layout)

    def _open_drawer(self, *args):
        nav_drawer = self.manager.parent.ids.get("nav_drawer") if hasattr(self.manager.parent, "ids") else None
        if nav_drawer:
            nav_drawer.set_state("open")

    def on_pre_enter(self):
        self._load_plans()

    def _load_plans(self, *args):
        """Load plans from API."""
        self.loading_box.height = dp(60)
        self.loading_spinner.active = True
        self.plans_list.clear_widgets()

        def _on_data(result, error):
            self.loading_box.height = dp(0)
            self.loading_spinner.active = False

            if error:
                self._show_placeholder(f"Erro: {error.message}")
                return

            if result:
                plans = result.get("plans", result if isinstance(result, list) else [])
                self._plans = plans
                self._update_list()

        api_client.get_plans_async(_on_data)

    def _update_list(self):
        """Update the plans list display."""
        self.plans_list.clear_widgets()

        if not self._plans:
            self._show_placeholder("Nenhum plano encontrado")
            return

        for plan in self._plans:
            card = PlanCard(plan_data=plan)
            self.plans_list.add_widget(card)

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
        self.plans_list.add_widget(label)

    def _create_plan(self, *args):
        """Open dialog to create a new plan."""
        self._open_plan_dialog()

    def edit_plan(self, plan_data):
        """Open dialog to edit a plan."""
        self._open_plan_dialog(plan_data)

    def _open_plan_dialog(self, plan_data=None):
        """Open plan create/edit dialog."""
        is_edit = plan_data is not None
        title = "Editar Plano" if is_edit else "Novo Plano"

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(480),
            padding=dp(8),
        )

        # Name
        name_field = MDTextField(
            hint_text="Nome do plano",
            text=plan_data.get("name", "") if is_edit else "",
            mode="round",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(8)],
        )
        content.add_widget(name_field)

        # Description
        desc_field = MDTextField(
            hint_text="Descricao",
            text=plan_data.get("description", "") if is_edit else "",
            mode="round",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(8)],
        )
        content.add_widget(desc_field)

        # Prices row
        prices_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(56),
        )

        price_monthly_field = MDTextField(
            hint_text="Preco mensal (R$)",
            text=str(plan_data.get("price_monthly", 0)) if is_edit else "0",
            mode="round",
            input_filter="float",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(8)],
            size_hint_x=0.5,
        )
        prices_row.add_widget(price_monthly_field)

        price_yearly_field = MDTextField(
            hint_text="Preco anual (R$)",
            text=str(plan_data.get("price_yearly", 0)) if is_edit else "0",
            mode="round",
            input_filter="float",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(8)],
            size_hint_x=0.5,
        )
        prices_row.add_widget(price_yearly_field)
        content.add_widget(prices_row)

        # Limits row
        limits_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(56),
        )

        max_bots_field = MDTextField(
            hint_text="Max bots",
            text=str(plan_data.get("max_bots", 1)) if is_edit else "1",
            mode="round",
            input_filter="int",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(8)],
            size_hint_x=0.5,
        )
        limits_row.add_widget(max_bots_field)

        max_msgs_field = MDTextField(
            hint_text="Max mensagens/mes",
            text=str(plan_data.get("max_messages_per_month", 500)) if is_edit else "500",
            mode="round",
            input_filter="int",
            hint_text_color_normal=Colors.TEXT_HINT,
            line_color_normal=Colors.BG_INPUT,
            line_color_focus=Colors.PRIMARY_LIGHT,
            text_color_normal=Colors.TEXT_PRIMARY,
            text_color_focus=Colors.TEXT_PRIMARY,
            fill_color_normal=Colors.BG_INPUT,
            radius=[dp(8)],
            size_hint_x=0.5,
        )
        limits_row.add_widget(max_msgs_field)
        content.add_widget(limits_row)

        # Feature toggles
        toggles_label = MDLabel(
            text="[b]Recursos[/b]",
            markup=True,
            font_style="Subtitle2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(24),
        )
        content.add_widget(toggles_label)

        # LLM toggle
        llm_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
            spacing=dp(8),
        )
        llm_row.add_widget(MDLabel(
            text="LLM",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        ))
        llm_row.add_widget(MDBoxLayout())
        llm_switch = MDSwitch(
            active=plan_data.get("has_llm", False) if is_edit else False,
            pos_hint={"center_y": 0.5},
        )
        llm_row.add_widget(llm_switch)
        content.add_widget(llm_row)

        # Flora AI toggle
        flora_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
            spacing=dp(8),
        )
        flora_row.add_widget(MDLabel(
            text="Flora AI",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        ))
        flora_row.add_widget(MDBoxLayout())
        flora_switch = MDSwitch(
            active=plan_data.get("has_flora_ai", False) if is_edit else False,
            pos_hint={"center_y": 0.5},
        )
        flora_row.add_widget(flora_switch)
        content.add_widget(flora_row)

        # Media toggle
        media_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
            spacing=dp(8),
        )
        media_row.add_widget(MDLabel(
            text="Midia (imagens, audio)",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        ))
        media_row.add_widget(MDBoxLayout())
        media_switch = MDSwitch(
            active=plan_data.get("has_media", False) if is_edit else False,
            pos_hint={"center_y": 0.5},
        )
        media_row.add_widget(media_switch)
        content.add_widget(media_row)

        def _save_plan(*args):
            data = {
                "name": name_field.text.strip(),
                "description": desc_field.text.strip(),
                "price_monthly": float(price_monthly_field.text or 0),
                "price_yearly": float(price_yearly_field.text or 0),
                "max_bots": int(max_bots_field.text or 1),
                "max_messages_per_month": int(max_msgs_field.text or 500),
                "has_llm": llm_switch.active,
                "has_flora_ai": flora_switch.active,
                "has_media": media_switch.active,
            }

            if not data["name"]:
                return

            if is_edit:
                api_client.update_plan(plan_data.get("id"), data)
            else:
                api_client.create_plan(data)

            dialog.dismiss()
            Clock.schedule_once(lambda dt: self._load_plans(), 0.5)

        dialog = MDDialog(
            title=title,
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
                    text="SALVAR",
                    md_bg_color=Colors.PRIMARY,
                    text_color=Colors.TEXT_PRIMARY,
                    on_release=_save_plan,
                ),
            ],
        )
        dialog.open()

    def delete_plan(self, plan_data):
        """Confirm and delete a plan."""
        plan_id = plan_data.get("id", "")
        plan_name = plan_data.get("name", "")

        def _confirm_delete(*args):
            api_client.delete_plan(plan_id)
            confirm_dialog.dismiss()
            Clock.schedule_once(lambda dt: self._load_plans(), 0.5)

        confirm_dialog = MDDialog(
            title="Excluir Plano",
            text=f"Tem certeza que deseja excluir o plano '{plan_name}'?",
            buttons=[
                MDFlatButton(
                    text="CANCELAR",
                    theme_text_color="Custom",
                    text_color=Colors.TEXT_SECONDARY,
                    on_release=lambda x: confirm_dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="EXCLUIR",
                    md_bg_color=Colors.ERROR,
                    text_color=Colors.TEXT_PRIMARY,
                    on_release=_confirm_delete,
                ),
            ],
        )
        confirm_dialog.open()
