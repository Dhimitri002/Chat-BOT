# ═══════════════════════════════════════════════════════════════
# Flora Platform — Componentes Estilizados (KivyMD)
# ═══════════════════════════════════════════════════════════════
# Funções fábrica que retornam widgets KivyMD pré-configurados
# com o tema escuro premium da Flora Platform.
# ═══════════════════════════════════════════════════════════════

from typing import Callable, List, Optional, Tuple

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, StringProperty

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.chip import MDChip
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.relativelayout import MDRelativeLayout

from apps.shared.theme import FloraColors, FloraTheme

# Instância de cores para uso nos componentes
_colors = FloraColors()


# ═══════════════════════════════════════════════════════════════
# Card Estilizado
# ═══════════════════════════════════════════════════════════════

def StyledCard(
    radius: int = 16,
    elevation: int = 4,
    md_bg_color: Optional[Tuple[float, ...]] = None,
    padding: int = 16,
    orientation: str = "vertical",
    ripple_behavior: bool = False,
    line_color: Optional[Tuple[float, ...]] = None,
    **kwargs,
) -> MDCard:
    """Cria um MDCard com estilo premium Flora.

    Args:
        radius: Raio dos cantos arredondados (dp).
        elevation: Nível de elevação/sombra.
        md_bg_color: Cor de fundo RGBA. Padrão: SURFACE_CARD.
        padding: Padding interno (dp).
        orientation: Orientação do layout ('vertical' ou 'horizontal').
        ripple_behavior: Se True, ativa efeito ripple ao toque.
        line_color: Cor da borda do card.
        **kwargs: Argumentos adicionais para MDCard.

    Returns:
        MDCard configurado.
    """
    card = MDCard(
        radius=[dp(radius)],
        elevation=elevation,
        md_bg_color=md_bg_color or _colors.to_rgba(FloraColors.SURFACE_CARD),
        padding=dp(padding),
        orientation=orientation,
        ripple_behavior=ripple_behavior,
        line_color=line_color or _colors.to_rgba(FloraColors.DIVIDER),
        **kwargs,
    )
    return card


# ═══════════════════════════════════════════════════════════════
# Botão Estilizado
# ═══════════════════════════════════════════════════════════════

def StyledButton(
    text: str = "",
    button_type: str = "raised",
    bg_color: Optional[Tuple[float, ...]] = None,
    text_color: Tuple[float, ...] = (1, 1, 1, 1),
    radius: int = 12,
    font_size: int = 14,
    bold: bool = True,
    on_release: Optional[Callable] = None,
    icon: str = "",
    size_hint_x: Optional[float] = None,
    size_hint_y: Optional[float] = None,
    width: Optional[float] = None,
    **kwargs,
) -> MDRaisedButton:
    """Cria um botão estilizado com tema Flora.

    Args:
        text: Texto do botão.
        button_type: Tipo do botão ('raised', 'flat', 'icon').
        bg_color: Cor de fundo RGBA. Padrão: PRIMARY_PURPLE.
        text_color: Cor do texto RGBA.
        radius: Raio dos cantos (dp).
        font_size: Tamanho da fonte (sp).
        bold: Se True, texto em negrito.
        on_release: Callback ao pressionar.
        icon: Ícone Material Design (para tipo 'icon').
        size_hint_x: Largura relativa.
        size_hint_y: Altura relativa.
        width: Largura fixa (dp).
        **kwargs: Argumentos adicionais.

    Returns:
        Botão configurado.
    """
    bg = bg_color or _colors.to_rgba(FloraColors.PRIMARY_PURPLE)
    font_style = "Button"

    if button_type == "flat":
        btn = MDRectangleFlatButton(
            text=text,
            text_color=text_color,
            line_color=bg,
            font_size=sp(font_size),
            size_hint_x=size_hint_x,
            size_hint_y=size_hint_y,
            width=dp(width) if width else None,
            **kwargs,
        )
    elif button_type == "icon":
        btn = MDIconButton(
            icon=icon,
            icon_color=text_color,
            md_bg_color=bg,
            size_hint_x=size_hint_x,
            size_hint_y=size_hint_y,
            **kwargs,
        )
    else:
        btn = MDRaisedButton(
            text=text,
            md_bg_color=bg,
            text_color=text_color,
            font_size=sp(font_size),
            elevation=2,
            size_hint_x=size_hint_x,
            size_hint_y=size_hint_y,
            width=dp(width) if width else None,
            **kwargs,
        )

    if on_release:
        btn.bind(on_release=on_release)

    return btn


# ═══════════════════════════════════════════════════════════════
# Campo de Texto Estilizado
# ═══════════════════════════════════════════════════════════════

def StyledInput(
    hint_text: str = "",
    text: str = "",
    helper_text: str = "",
    helper_text_mode: str = "on_focus",
    icon_left: str = "",
    icon_right: str = "",
    icon_color: Optional[Tuple[float, ...]] = None,
    line_color: Optional[Tuple[float, ...]] = None,
    text_color: Optional[Tuple[float, ...]] = None,
    hint_color: Optional[Tuple[float, ...]] = None,
    mode: str = "rectangle",
    size_hint_x: Optional[float] = None,
    password: bool = False,
    required: bool = False,
    max_text_length: Optional[int] = None,
    **kwargs,
) -> MDTextField:
    """Cria um MDTextField com estilo premium Flora.

    Args:
        hint_text: Texto de placeholder.
        text: Texto inicial.
        helper_text: Texto de ajuda abaixo do campo.
        helper_text_mode: Modo do helper text ('on_focus', 'persistent', 'on_error').
        icon_left: Ícone à esquerda.
        icon_right: Ícone à direita.
        icon_color: Cor dos ícones RGBA.
        line_color: Cor da linha inferior RGBA.
        text_color: Cor do texto digitado RGBA.
        hint_color: Cor do placeholder RGBA.
        mode: Modo do campo ('rectangle', 'fill', 'line', 'round').
        size_hint_x: Largura relativa.
        password: Se True, modo senha.
        required: Se True, campo obrigatório.
        max_text_length: Limite de caracteres.
        **kwargs: Argumentos adicionais.

    Returns:
        MDTextField configurado.
    """
    field = MDTextField(
        hint_text=hint_text,
        text=text,
        helper_text=helper_text,
        helper_text_mode=helper_text_mode,
        icon_left=icon_left,
        icon_right=icon_right,
        icon_color_active=icon_color or _colors.to_rgba(FloraColors.PRIMARY_PURPLE),
        icon_color_normal=icon_color or _colors.to_rgba(FloraColors.TEXT_TERTIARY),
        line_color_focus=line_color or _colors.to_rgba(FloraColors.PRIMARY_PURPLE),
        line_color_normal=_colors.to_rgba(FloraColors.DIVIDER),
        text_color_normal=text_color or _colors.to_rgba(FloraColors.TEXT_PRIMARY),
        text_color_focus=text_color or _colors.to_rgba(FloraColors.TEXT_PRIMARY),
        hint_text_color_normal=hint_color or _colors.to_rgba(FloraColors.TEXT_HINT),
        hint_text_color_focus=hint_color or _colors.to_rgba(FloraColors.PRIMARY_PURPLE_LIGHT),
        mode=mode,
        size_hint_x=size_hint_x,
        password=password,
        required=required,
        max_text_length=max_text_length,
        md_bg_color=_colors.to_rgba(FloraColors.SURFACE_INPUT),
        **kwargs,
    )
    return field


# ═══════════════════════════════════════════════════════════════
# Label Estilizado
# ═══════════════════════════════════════════════════════════════

def StyledLabel(
    text: str = "",
    font_style: str = "Body1",
    color: Optional[Tuple[float, ...]] = None,
    halign: str = "left",
    bold: bool = False,
    italic: bool = False,
    font_size: Optional[int] = None,
    theme_text_color: str = "Custom",
    shorten: bool = False,
    max_lines: int = 0,
    **kwargs,
) -> MDLabel:
    """Cria um MDLabel com estilo Flora.

    Args:
        text: Texto do label.
        font_style: Estilo de fonte KivyMD ('H1'-'H6', 'Subtitle1', 'Body1', etc.).
        color: Cor do texto RGBA. Padrão: TEXT_PRIMARY.
        halign: Alinhamento horizontal ('left', 'center', 'right').
        bold: Se True, texto em negrito.
        italic: Se True, texto em itálico.
        font_size: Tamanho da fonte em sp (sobrescreve font_style).
        theme_text_color: Tema de texto ('Primary', 'Secondary', 'Hint', 'Custom').
        shorten: Se True, trunca texto longo com '...'.
        max_lines: Número máximo de linhas (0 = sem limite).
        **kwargs: Argumentos adicionais.

    Returns:
        MDLabel configurado.
    """
    label = MDLabel(
        text=text,
        font_style=font_style,
        theme_text_color=theme_text_color,
        text_color=color or _colors.to_rgba(FloraColors.TEXT_PRIMARY),
        halign=halign,
        shorten=shorten,
        max_lines=max_lines if max_lines > 0 else None,
        **kwargs,
    )

    if bold:
        label.bold = True
    if italic:
        label.italic = True
    if font_size:
        label.font_size = sp(font_size)

    return label


# ═══════════════════════════════════════════════════════════════
# Bolha de Chat
# ═══════════════════════════════════════════════════════════════

def ChatBubble(
    text: str = "",
    is_sent: bool = True,
    timestamp: str = "",
    radius: int = 16,
    max_width: float = 0.75,
    **kwargs,
) -> MDCard:
    """Cria uma bolha de mensagem de chat.

    Args:
        text: Conteúdo da mensagem.
        is_sent: True se mensagem enviada, False se recebida.
        timestamp: Horário da mensagem (ex: '14:30').
        radius: Raio dos cantos (dp).
        max_width: Largura máxima como fração da tela (0-1).
        **kwargs: Argumentos adicionais.

    Returns:
        MDCard contendo a bolha de chat.
    """
    bg_color = (
        _colors.to_rgba(FloraColors.CHAT_SENT)
        if is_sent
        else _colors.to_rgba(FloraColors.CHAT_RECEIVED)
    )
    text_color = (
        _colors.to_rgba(FloraColors.CHAT_TEXT_SENT)
        if is_sent
        else _colors.to_rgba(FloraColors.CHAT_TEXT_RECEIVED)
    )
    halign = "right" if is_sent else "left"

    # Layout interno
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.label import MDLabel

    inner = MDBoxLayout(
        orientation="vertical",
        adaptive_height=True,
        padding=[dp(12), dp(8)],
    )

    msg_label = MDLabel(
        text=text,
        theme_text_color="Custom",
        text_color=text_color,
        halign=halign,
        adaptive_height=True,
        markup=True,
    )
    inner.add_widget(msg_label)

    if timestamp:
        time_label = MDLabel(
            text=timestamp,
            theme_text_color="Custom",
            text_color=_colors.to_rgba(FloraColors.TEXT_TERTIARY),
            halign=halign,
            font_style="Caption",
            adaptive_height=True,
        )
        inner.add_widget(time_label)

    bubble = MDCard(
        md_bg_color=bg_color,
        radius=[dp(radius)],
        padding=dp(2),
        size_hint_x=max_width,
        size_hint_y=None,
        height=inner.height + dp(4),
        elevation=1,
        **kwargs,
    )
    bubble.add_widget(inner)

    return bubble


# ═══════════════════════════════════════════════════════════════
# Chip de Status
# ═══════════════════════════════════════════════════════════════

def StatusChip(
    text: str = "",
    status: str = "active",
    font_size: int = 11,
    **kwargs,
) -> MDChip:
    """Cria um chip colorido para indicar status.

    Args:
        text: Texto do chip.
        status: Tipo de status ('active', 'pending', 'expired', 'suspended',
                'success', 'warning', 'error', 'info').
        font_size: Tamanho da fonte (sp).
        **kwargs: Argumentos adicionais.

    Returns:
        MDChip configurado.
    """
    status_colors = {
        "active": _colors.to_rgba(FloraColors.STATUS_ACTIVE),
        "pending": _colors.to_rgba(FloraColors.STATUS_PENDING),
        "expired": _colors.to_rgba(FloraColors.STATUS_EXPIRED),
        "suspended": _colors.to_rgba(FloraColors.STATUS_SUSPENDED),
        "success": _colors.to_rgba(FloraColors.SUCCESS),
        "warning": _colors.to_rgba(FloraColors.WARNING),
        "error": _colors.to_rgba(FloraColors.ERROR),
        "info": _colors.to_rgba(FloraColors.INFO),
    }

    chip_color = status_colors.get(status, _colors.to_rgba(FloraColors.INFO))

    chip = MDChip(
        label=text,
        icon="",
        text_color=(1, 1, 1, 1),
        color=chip_color,
        font_size=sp(font_size),
        **kwargs,
    )
    return chip


# ═══════════════════════════════════════════════════════════════
# Avatar Circular
# ═══════════════════════════════════════════════════════════════

def AvatarWidget(
    initials: str = "?",
    size: int = 40,
    bg_color: Optional[Tuple[float, ...]] = None,
    text_color: Tuple[float, ...] = (1, 1, 1, 1),
    font_size: int = 14,
    **kwargs,
) -> MDCard:
    """Cria um avatar circular com iniciais.

    Args:
        initials: Iniciais a exibir (ex: 'JD' para João da Silva).
        size: Diâmetro do avatar (dp).
        bg_color: Cor de fundo RGBA. Padrão: PRIMARY_PURPLE.
        text_color: Cor do texto RGBA.
        font_size: Tamanho da fonte (sp).
        **kwargs: Argumentos adicionais.

    Returns:
        MDCard circular com as iniciais centralizadas.
    """
    from apps.shared.utils import generate_avatar_color

    bg = bg_color or generate_avatar_color(initials)

    avatar = MDCard(
        size=(dp(size), dp(size)),
        radius=[dp(size / 2)],
        md_bg_color=bg,
        elevation=2,
        **kwargs,
    )

    label = MDLabel(
        text=initials.upper()[:2],
        halign="center",
        valign="center",
        theme_text_color="Custom",
        text_color=text_color,
        font_style="Subtitle2",
        bold=True,
        font_size=sp(font_size),
    )
    avatar.add_widget(label)

    return avatar


# ═══════════════════════════════════════════════════════════════
# Card de Estatística (Dashboard)
# ═══════════════════════════════════════════════════════════════

def stat_card(
    title: str = "",
    value: str = "0",
    icon: str = "chart-line",
    trend: str = "",
    trend_positive: bool = True,
    bg_color: Optional[Tuple[float, ...]] = None,
    **kwargs,
) -> MDCard:
    """Cria um card de métrica para dashboards.

    Args:
        title: Título da métrica (ex: 'Clientes Ativos').
        value: Valor principal (ex: '1.234').
        icon: Ícone Material Design.
        trend: Texto de tendência (ex: '+12%').
        trend_positive: True se tendência positiva, False se negativa.
        bg_color: Cor de fundo RGBA.
        **kwargs: Argumentos adicionais.

    Returns:
        MDCard com layout de métrica.
    """
    card = MDCard(
        orientation="vertical",
        padding=dp(16),
        radius=dp(16),
        elevation=3,
        md_bg_color=bg_color or _colors.to_rgba(FloraColors.SURFACE_CARD),
        size_hint_y=None,
        height=dp(120),
        **kwargs,
    )

    # Linha superior: ícone + título
    top_row = MDBoxLayout(
        orientation="horizontal",
        adaptive_height=True,
        spacing=dp(8),
    )

    icon_label = MDLabel(
        text=f"[font=Icons]{icon}[/font]",
        markup=True,
        theme_text_color="Custom",
        text_color=_colors.to_rgba(FloraColors.PRIMARY_PURPLE),
        font_style="Icon",
        size_hint_x=None,
        width=dp(32),
    )
    top_row.add_widget(icon_label)

    title_label = MDLabel(
        text=title,
        theme_text_color="Custom",
        text_color=_colors.to_rgba(FloraColors.TEXT_SECONDARY),
        font_style="Caption",
        adaptive_height=True,
    )
    top_row.add_widget(title_label)
    card.add_widget(top_row)

    # Valor principal
    value_label = MDLabel(
        text=str(value),
        theme_text_color="Custom",
        text_color=_colors.to_rgba(FloraColors.TEXT_PRIMARY),
        font_style="H4",
        bold=True,
        adaptive_height=True,
    )
    card.add_widget(value_label)

    # Tendência (opcional)
    if trend:
        trend_color = (
            _colors.to_rgba(FloraColors.SUCCESS)
            if trend_positive
            else _colors.to_rgba(FloraColors.ERROR)
        )
        trend_label = MDLabel(
            text=trend,
            theme_text_color="Custom",
            text_color=trend_color,
            font_style="Caption",
            adaptive_height=True,
        )
        card.add_widget(trend_label)

    return card


# ═══════════════════════════════════════════════════════════════
# Item de Navegação (Sidebar / Drawer)
# ═══════════════════════════════════════════════════════════════

def navigation_item(
    text: str = "",
    icon: str = "circle",
    on_release: Optional[Callable] = None,
    active: bool = False,
    badge_text: str = "",
    **kwargs,
) -> MDBoxLayout:
    """Cria um item de navegação para sidebar ou drawer.

    Args:
        text: Texto do item.
        icon: Ícone Material Design.
        on_release: Callback ao pressionar.
        active: Se True, destaca como item ativo.
        badge_text: Texto de badge (notificação/contador).
        **kwargs: Argumentos adicionais.

    Returns:
        MDBoxLayout com o item de navegação.
    """
    bg_color = (
        _colors.to_rgba(FloraColors.PRIMARY_PURPLE)
        if active
        else _colors.to_rgba(FloraColors.TRANSPARENT)
    )
    text_color = (
        _colors.to_rgba(FloraColors.TEXT_PRIMARY)
        if active
        else _colors.to_rgba(FloraColors.TEXT_SECONDARY)
    )
    icon_color = (
        _colors.to_rgba(FloraColors.TEXT_PRIMARY)
        if active
        else _colors.to_rgba(FloraColors.TEXT_TERTIARY)
    )

    item = MDBoxLayout(
        orientation="horizontal",
        adaptive_height=True,
        padding=[dp(16), dp(12)],
        spacing=dp(12),
        md_bg_color=bg_color,
        radius=[dp(12)],
        **kwargs,
    )

    # Ícone
    icon_label = MDLabel(
        text=f"[font=Icons]{icon}[/font]",
        markup=True,
        theme_text_color="Custom",
        text_color=icon_color,
        font_style="Icon",
        size_hint_x=None,
        width=dp(32),
        halign="center",
    )
    item.add_widget(icon_label)

    # Texto
    text_label = MDLabel(
        text=text,
        theme_text_color="Custom",
        text_color=text_color,
        font_style="Body1",
        adaptive_height=True,
        halign="left",
        bold=active,
    )
    item.add_widget(text_label)

    # Badge (opcional)
    if badge_text:
        badge = MDLabel(
            text=badge_text,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="Caption",
            halign="center",
            size_hint_x=None,
            width=dp(24),
        )
        badge_card = MDCard(
            md_bg_color=_colors.to_rgba(FloraColors.ACCENT_PINK),
            radius=[dp(10)],
            size=(dp(24), dp(20)),
            elevation=0,
        )
        badge_card.add_widget(badge)
        item.add_widget(badge_card)

    if on_release:
        item.bind(on_touch_down=lambda inst, touch: on_release(inst)
                  if inst.collide_point(*touch.pos) else None)

    return item
