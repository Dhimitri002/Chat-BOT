# ═══════════════════════════════════════════════════════════════
# Flora Platform — Tema Escuro (KivyMD Theme)
# ═══════════════════════════════════════════════════════════════
# Configuração de tema escuro premium para KivyMD.
# Cores definidas como constantes e classe de tema aplicável.
# ═══════════════════════════════════════════════════════════════

from dataclasses import dataclass
from typing import Dict


# ═══════════════════════════════════════════════════════════════
# Paleta de Cores — Flora Platform
# ═══════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class FloraColors:
    """Paleta de cores completa da Flora Platform.

    Agrupa todas as cores utilizadas nos aplicativos KivyMD.
    Os valores são tuplas RGBA (0-1) para compatibilidade com Kivy.
    """

    # ── Primárias ─────────────────────────────────────────────
    PRIMARY_PURPLE: str = "#6C63FF"
    PRIMARY_PURPLE_DARK: str = "#5A52D5"
    PRIMARY_PURPLE_LIGHT: str = "#8B83FF"

    # ── Acento ────────────────────────────────────────────────
    ACCENT_PINK: str = "#FF6B9D"
    ACCENT_PINK_DARK: str = "#E55A88"
    ACCENT_PINK_LIGHT: str = "#FF8AB5"

    # ── Fundo Escuro ──────────────────────────────────────────
    BG_DARKEST: str = "#0D0D1A"
    BG_DARK: str = "#1A1A2E"
    BG_MEDIUM: str = "#16213E"
    BG_LIGHT: str = "#0F3460"
    BG_LIGHTEST: str = "#1A2A4A"

    # ── Superfícies ───────────────────────────────────────────
    SURFACE_CARD: str = "#1E1E3A"
    SURFACE_DIALOG: str = "#24244A"
    SURFACE_INPUT: str = "#12122A"
    SURFACE_HOVER: str = "#2A2A4E"

    # ── Texto ─────────────────────────────────────────────────
    TEXT_PRIMARY: str = "#FFFFFF"
    TEXT_SECONDARY: str = "#B0B0CC"
    TEXT_TERTIARY: str = "#707099"
    TEXT_DISABLED: str = "#4A4A6A"
    TEXT_HINT: str = "#5A5A80"

    # ── Status ────────────────────────────────────────────────
    SUCCESS: str = "#4CAF50"
    SUCCESS_DARK: str = "#388E3C"
    WARNING: str = "#FFC107"
    WARNING_DARK: str = "#FFA000"
    ERROR: str = "#FF5252"
    ERROR_DARK: str = "#D32F2F"
    INFO: str = "#2196F3"
    INFO_DARK: str = "#1565C0"

    # ── Gradientes (tuplas de cores hex) ──────────────────────
    GRADIENT_PRIMARY: tuple = ("#6C63FF", "#FF6B9D")
    GRADIENT_DARK: tuple = ("#1A1A2E", "#0F3460")
    GRADIENT_SURFACE: tuple = ("#1E1E3A", "#24244A")

    # ── Misc ──────────────────────────────────────────────────
    DIVIDER: str = "#2A2A4E"
    OVERLAY: str = "#00000080"
    RIPPLE: str = "#FFFFFF11"
    WHITE: str = "#FFFFFF"
    BLACK: str = "#000000"
    TRANSPARENT: str = "#00000000"

    # ── Status de Chat ────────────────────────────────────────
    CHAT_SENT: str = "#6C63FF"
    CHAT_RECEIVED: str = "#1E1E3A"
    CHAT_TEXT_SENT: str = "#FFFFFF"
    CHAT_TEXT_RECEIVED: str = "#E0E0F0"

    # ── Status de Assinatura ──────────────────────────────────
    STATUS_ACTIVE: str = "#4CAF50"
    STATUS_PENDING: str = "#FFC107"
    STATUS_EXPIRED: str = "#FF5252"
    STATUS_SUSPENDED: str = "#9E9E9E"

    # ── WhatsApp ──────────────────────────────────────────────
    WA_CONNECTED: str = "#25D366"
    WA_DISCONNECTED: str = "#F44336"
    WA_CONNECTING: str = "#FF9800"

    def to_rgba(self, hex_color: str) -> tuple:
        """Converte cor hexadecimal para tupla RGBA (0-1).

        Args:
            hex_color: Cor em formato '#RRGGBB' ou '#RRGGBBAA'.

        Returns:
            Tupla (R, G, B, A) com valores normalizados entre 0 e 1.
        """
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255
            return (r, g, b, 1.0)
        elif len(hex_color) == 8:
            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255
            a = int(hex_color[6:8], 16) / 255
            return (r, g, b, a)
        raise ValueError(f"Formato de cor invalido: #{hex_color}")

    def to_dict(self) -> Dict[str, str]:
        """Retorna todas as cores como dicionario nome -> hex."""
        return {
            k: v for k, v in self.__dict__.items()
            if isinstance(v, str) and k.isupper()
        }

    @staticmethod
    def get_status_color(status: str) -> tuple:
        """Retorna a cor RGBA correspondente a um status.

        Args:
            status: Nome do status ('active', 'pending', 'expired', etc.)

        Returns:
            Tupla RGBA (0-1).
        """
        c = FloraColors()
        status_map = {
            "connected": c.WA_CONNECTED,
            "active": c.STATUS_ACTIVE,
            "disconnected": c.WA_DISCONNECTED,
            "connecting": c.WA_CONNECTING,
            "error": c.ERROR,
            "expired": c.STATUS_EXPIRED,
            "revoked": c.ERROR,
            "pending": c.STATUS_PENDING,
        }
        hex_color = status_map.get(status.lower(), c.TEXT_TERTIARY)
        return c.to_rgba(hex_color)

    @staticmethod
    def get_status_text(status: str) -> str:
        """Retorna o texto legivel de um status.

        Args:
            status: Nome interno do status.

        Returns:
            Texto formatado em Portugues.
        """
        text_map = {
            "connected": "Conectado",
            "active": "Ativo",
            "disconnected": "Desconectado",
            "connecting": "Conectando...",
            "error": "Erro",
            "expired": "Expirado",
            "revoked": "Revogado",
            "pending": "Pendente",
        }
        return text_map.get(status.lower(), status.capitalize())


# ═══════════════════════════════════════════════════════════════
# Tema KivyMD — Configuração do App
# ═══════════════════════════════════════════════════════════════


class FloraTheme:
    """Gerenciador de tema escuro para aplicativos KivyMD da Flora.

    Uso:
        class FloraApp(MDApp):
            def build(self):
                self.theme = FloraTheme.apply(self)

    Aplica o tema escuro com as cores da paleta Flora.
    """

    colors = FloraTheme.__dict__.get("colors", FloraColors())

    # Configurações padrão do tema
    THEME_STYLE: str = "Dark"
    PRIMARY_PALETTE: str = "DeepPurple"
    PRIMARY_HUE: str = "A400"
    ACCENT_PALETTE: str = "Pink"
    ACCENT_HUE: str = "A200"

    # Dimensões padrão
    CARD_RADIUS: int = 16
    CARD_ELEVATION: int = 2
    BUTTON_RADIUS: int = 12
    INPUT_RADIUS: int = 10
    PADDING: int = 16
    SPACING: int = 8
    ICON_SIZE: int = 24
    AVATAR_SIZE: int = 48

    # Font sizes
    FONT_H1: int = 28
    FONT_H2: int = 24
    FONT_H3: int = 20
    FONT_BODY: int = 14
    FONT_CAPTION: int = 12
    FONT_SMALL: int = 10

    # Transitions
    TRANSITION_FAST: float = 0.15
    TRANSITION_NORMAL: float = 0.25
    TRANSITION_SLOW: float = 0.4

    # Mapeamento de cores customizadas para o tema KivyMD
    CUSTOM_COLORS: Dict[str, tuple] = {
        "Primary": (0.424, 0.388, 1.0, 1.0),        # #6C63FF
        "Accent": (1.0, 0.420, 0.616, 1.0),           # #FF6B9D
        "Background": (0.102, 0.102, 0.180, 1.0),     # #1A1A2E
        "Surface": (0.086, 0.129, 0.243, 1.0),        # #16213E
        "SurfaceCard": (0.118, 0.118, 0.227, 1.0),    # #1E1E3A
        "Success": (0.298, 0.686, 0.314, 1.0),        # #4CAF50
        "Warning": (1.0, 0.757, 0.027, 1.0),          # #FFC107
        "Error": (1.0, 0.322, 0.322, 1.0),            # #FF5252
        "Info": (0.129, 0.588, 0.953, 1.0),           # #2196F3
        "TextPrimary": (1.0, 1.0, 1.0, 1.0),          # #FFFFFF
        "TextSecondary": (0.690, 0.690, 0.800, 1.0),  # #B0B0CC
        "TextTertiary": (0.439, 0.439, 0.600, 1.0),   # #707099
    }

    @classmethod
    def apply(cls, app) -> None:
        """Aplica o tema escuro Flora ao aplicativo KivyMD.

        Args:
            app: Instancia de MDApp do KivyMD.
        """
        theme = app.theme_cls if hasattr(app, "theme_cls") else app

        # Modo escuro
        theme.theme_style = cls.THEME_STYLE

        # Paleta primária
        theme.primary_palette = cls.PRIMARY_PALETTE
        theme.primary_hue = cls.PRIMARY_HUE

        # Paleta de acento
        theme.accent_palette = cls.ACCENT_PALETTE
        theme.accent_hue = cls.ACCENT_HUE

        # Cores de fundo customizadas
        theme.bg_dark = cls.colors.to_rgba(FloraColors.BG_DARK)
        theme.bg_darkest = cls.colors.to_rgba(FloraColors.BG_DARKEST)
        theme.bg_normal = cls.colors.to_rgba(FloraColors.BG_MEDIUM)
        theme.bg_light = cls.colors.to_rgba(FloraColors.BG_LIGHT)

    @classmethod
    def get_color(cls, name: str) -> tuple:
        """Retorna uma cor customizada pelo nome.

        Args:
            name: Nome da cor (ex: 'Primary', 'Accent', 'Background').

        Returns:
            Tupla RGBA (0-1).
        """
        return cls.CUSTOM_COLORS.get(name, (1, 1, 1, 1))

    @classmethod
    def get_hex(cls, name: str) -> str:
        """Retorna uma cor pelo nome no formato hexadecimal.

        Args:
            name: Nome do atributo da FloraColors (ex: 'PRIMARY_PURPLE').

        Returns:
            String hexadecimal da cor.
        """
        return getattr(FloraColors, name, "#FFFFFF")
