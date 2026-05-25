"""
PlansScreen — Admin plan management.

Fetches from GET /api/v1/plans which returns:
  [ { "id", "name", "description", "price", "currency", "interval",
      "max_bots", "max_messages_per_month", "max_whatsapp_connections",
      "is_active", "created_at" } ]
"""

from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog

from app_admin.styles.theme import Colors, Theme


class PlansScreen(MDScreen):
    """List and manage subscription plans."""

    def __init__(self, app: "FloraAdminApp", **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._plans: list = []
        self._dialog: MDDialog | None = None
        self._build()

    # ── build UI ────────────────────────────────────────────────────────
    def _build(self):
        root = MDBoxLayout(
            orientation="vertical",
            padding=Theme.SPACE_LG,
            spacing=Theme.SPACE_MD,
            md_bg_color=Colors.BG_BASE,
        )

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=Theme.SPACE_SM,
        )
        header.add_widget(MDLabel(
            text="Planos",
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=0.7,
        ))
        header.add_widget(MDRaisedButton(
            text="Atualizar",
            size_hint_x=None,
            width=dp(120),
            md_bg_color=Colors.PRIMARY,
            text_color=Colors.BG_BASE,
            on_release=lambda *a: self.load_data(),
        ))
        root.add_widget(header)

        # Plan cards
        scroll = MDScrollView(do_scroll_x=False, bar_width=dp(2))
        self._list_container = MDBoxLayout(
            orientation="vertical",
            spacing=Theme.SPACE_LG,
            padding=[0, 0, 0, Theme.SPACE_LG],
            size_hint_y=None,
        )
        self._list_container.bind(minimum_height=self._list_container.setter("height"))
        scroll.add_widget(self._list_container)
        root.add_widget(scroll)

        self.add_widget(root)

    def on_enter(self, *args):
        if not self._plans:
            self.load_data()

    # ── data loading ─────────────────────────────────────────────────────
    def load_data(self):
        self._clear_list()
        spinner = MDSpinner(size_hint=(None, None), size=(dp(48), dp(48)))
        spinner.active = True
        self._list_container.add_widget(spinner)

        def _fetch():
            try:
                resp = self._app.api.list_plans()
                # Response may be a list directly or wrapped
                plans = resp if isinstance(resp, list) else resp.get("plans", [])
                Clock.schedule_once(lambda dt: self._render(plans), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, e=e: self._show_error(str(e)), 0)

        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _render(self, plans: list):
        self._plans = plans
        self._clear_list()

        if not plans:
            self._list_container.add_widget(MDLabel(
                text="Nenhum plano encontrado.",
                font_style="Body1",
                halign="center",
                theme_text_color="Custom",
                text_color=Colors.TEXT_HINT,
                size_hint_y=None,
                height=dp(48),
            ))
            return

        for plan in plans:
            card = self._build_plan_card(plan)
            self._list_container.add_widget(card)

    def _build_plan_card(self, plan: dict) -> MDCard:
        is_active = plan.get("is_active", False)
        price = plan.get("price", 0)
        currency = plan.get("currency", "BRL")
        interval = plan.get("interval", "month")
        max_bots = plan.get("max_bots", 0)
        max_msgs = plan.get("max_messages_per_month", 0)
        max_wa = plan.get("max_whatsapp_connections", 0)

        card = MDCard(
            orientation="vertical",
            padding=Theme.SPACE_LG,
            spacing=Theme.SPACE_SM,
            md_bg_color=Colors.BG_CARD,
            radius=[Theme.RADIUS_LARGE],
            elevation=Theme.ELEVATION_LOW,
            size_hint_y=None,
            height=dp(180),
        )

        # Top row: name + status
        top = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
        )
        top.add_widget(MDLabel(
            text=plan.get("name", "Sem nome"),
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
        ))
        top.add_widget(MDBoxLayout())  # spacer
        status_color_val = Colors.SUCCESS if is_active else Colors.TEXT_HINT
        status_text = "Ativo" if is_active else "Inativo"
        top.add_widget(MDLabel(
            text=status_text,
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=status_color_val,
            size_hint_x=None,
            width=dp(60),
        ))
        card.add_widget(top)

        # Description
        desc = plan.get("description", "Sem descrição")
        card.add_widget(MDLabel(
            text=desc,
            font_style="Body2",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            shorten=True,
            size_hint_y=None,
            height=dp(24),
        ))

        # Price row
        price_text = f"R$ {price:.2f}/{interval}" if currency == "BRL" else f"{currency} {price:.2f}/{interval}"
        accented = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
            padding=[Theme.SPACE_SM, 0],
        )
        accented.add_widget(MDLabel(
            text=price_text,
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=Colors.PRIMARY,
        ))
        card.add_widget(accented)

        # Features row
        features = MDBoxLayout(
            orientation="horizontal",
            spacing=Theme.SPACE_MD,
            size_hint_y=None,
            height=dp(24),
        )
        features.add_widget(MDLabel(
            text=f"  Bots: {max_bots}",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
        ))
        features.add_widget(MDLabel(
            text=f"  Msgs/mes: {max_msgs}",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
        ))
        features.add_widget(MDLabel(
            text=f"  WA: {max_wa}",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
        ))
        card.add_widget(features)

        # Actions
        actions = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
            spacing=dp(8),
            padding=[0, dp(4)],
        )
        actions.add_widget(MDBoxLayout())  # spacer
        actions.add_widget(MDIconButton(
            icon="pencil",
            theme_text_color="Custom",
            text_color=Colors.TEXT_SECONDARY,
            on_release=lambda *a, p=plan: self._edit_plan(p),
        ))
        if is_active:
            actions.add_widget(MDIconButton(
                icon="eye-off",
                theme_text_color="Custom",
                text_color=Colors.HIGHLIGHT,
                on_release=lambda *a, p=plan: self._deactivate_plan(p),
            ))
        card.add_widget(actions)

        card.bind(minimum_height=card.setter("height"))
        return card

    # ── actions ──────────────────────────────────────────────────────────
    def _edit_plan(self, plan: dict):
        self._app.show_snackbar(f"Editar plano: {plan.get('name', '')}")

    def _deactivate_plan(self, plan: dict):
        self._app.show_snackbar(f"Desativar plano: {plan.get('name', '')}")

    # ── helpers ──────────────────────────────────────────────────────────
    def _clear_list(self):
        self._list_container.clear_widgets()

    def _show_error(self, msg: str):
        self._clear_list()
        self._list_container.add_widget(MDLabel(
            text=f"Erro: {msg}",
            font_style="Body1",
            halign="center",
            theme_text_color="Custom",
            text_color=Colors.HIGHLIGHT,
        ))
