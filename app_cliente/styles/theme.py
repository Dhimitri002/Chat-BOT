"""
Flora Client App — Premium Dark Theme (Warm Edition)
=====================================================
Softer, warmer dark theme for the client-facing app.
Same design system as admin but with friendlier, cuter aesthetic.
"""

from kivy.utils import get_color_from_hex
from kivy.metrics import dp


# ═══════════════════════════════════════════════════════════════════════════════
#  COLOR PALETTE (Warm Edition)
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    """
    Warm, friendly dark color palette for the client app.
    Softer tones, warmer accents for the "cute" aesthetic.
    """

    # ── Background Layers ─────────────────────────────────────────────────
    BG_BASE         = get_color_from_hex("#13111a")   # Deep warm purple-black
    BG_SECONDARY    = get_color_from_hex("#1a1726")   # Slightly lighter
    BG_CARD         = get_color_from_hex("#211d2e")   # Card surface
    BG_INPUT        = get_color_from_hex("#282338")   # Input background
    BG_HOVER        = get_color_from_hex("#2e2842")   # Hover state
    BG_OVERLAY      = (0.07, 0.06, 0.1, 0.85)        # Modal overlay

    # ── Accent Colors (Warm Dracula) ─────────────────────────────────────
    PRIMARY         = get_color_from_hex("#ff79c6")   # Pink — primary
    PRIMARY_DARK    = get_color_from_hex("#e86db0")   # Darker pink
    PRIMARY_LIGHT   = get_color_from_hex("#ff9ad8")   # Lighter pink
    SECONDARY       = get_color_from_hex("#bd93f9")   # Purple — secondary
    SECONDARY_DARK  = get_color_from_hex("#a17be0")   # Darker purple
    TERTIARY        = get_color_from_hex("#6272a4")   # Comment blue

    # ── Text Colors ───────────────────────────────────────────────────────
    TEXT_PRIMARY    = get_color_from_hex("#f0f6fc")   # Near-white
    TEXT_SECONDARY  = get_color_from_hex("#9b8fb0")   # Warm muted purple-gray
    TEXT_HINT       = get_color_from_hex("#5a4f6a")   # Very muted
    TEXT_DISABLED   = get_color_from_hex("#3d3550")   # Disabled
    TEXT_ON_ACCENT  = get_color_from_hex("#13111a")   # Text on accent bg

    # ── Semantic Colors ───────────────────────────────────────────────────
    SUCCESS         = get_color_from_hex("#50fa7b")   # Bright green
    SUCCESS_LIGHT   = get_color_from_hex("#6aff95")   # Light green
    WARNING         = get_color_from_hex("#f1fa8c")   # Yellow
    WARNING_LIGHT   = get_color_from_hex("#f5ffaa")   # Light yellow
    ERROR           = get_color_from_hex("#ff5555")   # Bright red
    ERROR_LIGHT     = get_color_from_hex("#ff7b72")   # Light red
    INFO            = get_color_from_hex("#8be9fd")   # Cyan
    INFO_LIGHT      = get_color_from_hex("#a4f1ff")   # Light cyan

    # ── Legacy Aliases ───────────────────────────────────────────────────
    HIGHLIGHT       = get_color_from_hex("#ff5555")   # Maps to ERROR
    BG_CARD_ALT     = get_color_from_hex("#211d2e")   # Maps to BG_CARD

    # ── Gradient Pairs ───────────────────────────────────────────────────
    GRADIENT_PRIMARY   = [get_color_from_hex("#ff79c6"), get_color_from_hex("#bd93f9")]
    GRADIENT_SUCCESS   = [get_color_from_hex("#50fa7b"), get_color_from_hex("#6aff95")]
    GRADIENT_WARNING   = [get_color_from_hex("#f1fa8c"), get_color_from_hex("#f5ffaa")]
    GRADIENT_ERROR     = [get_color_from_hex("#ff5555"), get_color_from_hex("#ff7b72")]
    GRADIENT_INFO      = [get_color_from_hex("#8be9fd"), get_color_from_hex("#a4f1ff")]

    # ── Status Colors ────────────────────────────────────────────────────
    STATUS_CONNECTED    = get_color_from_hex("#50fa7b")
    STATUS_DISCONNECTED = get_color_from_hex("#ff5555")
    STATUS_PENDING      = get_color_from_hex("#f1fa8c")
    STATUS_ERROR        = get_color_from_hex("#ff5555")
    STATUS_ACTIVE       = get_color_from_hex("#50fa7b")
    STATUS_INACTIVE     = get_color_from_hex("#5a4f6a")


# ═══════════════════════════════════════════════════════════════════════════════
#  TYPOGRAPHY SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class Typography:
    """Typography scale — same as admin for consistency."""

    H1_SIZE = dp(32)
    H2_SIZE = dp(28)
    H3_SIZE = dp(24)
    H4_SIZE = dp(20)
    H5_SIZE = dp(18)
    H6_SIZE = dp(16)
    BODY_LARGE = dp(16)
    BODY = dp(14)
    BODY_SMALL = dp(12)
    CAPTION = dp(11)
    OVERLINE = dp(10)
    BUTTON = dp(14)

    H1 = "H1"
    H2 = "H2"
    H3 = "H3"
    H4 = "H4"
    H5 = "H5"
    H6 = "H6"
    SUBTITLE1 = "Subtitle1"
    SUBTITLE2 = "Subtitle2"
    BODY1 = "Body1"
    BODY2 = "Body2"
    CAPTION_STYLE = "Caption"
    OVERLINE_STYLE = "Overline"
    BUTTON_STYLE = "Button"

    WEIGHT_LIGHT = "300"
    WEIGHT_REGULAR = "400"
    WEIGHT_MEDIUM = "500"
    WEIGHT_BOLD = "bold"

    SPACING_TIGHT = -0.5
    SPACING_NORMAL = 0
    SPACING_WIDE = 0.5
    SPACING_EXTRA_WIDE = 1.0


# ═══════════════════════════════════════════════════════════════════════════════
#  SPACING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class Spacing:
    """Same spacing scale as admin."""
    XS   = dp(4)
    SM   = dp(8)
    MD   = dp(16)
    LG   = dp(24)
    XL   = dp(32)
    XXL  = dp(48)
    XXXL = dp(64)

    SPACE_XS   = dp(4)
    SPACE_SM   = dp(8)
    SPACE_MD   = dp(16)
    SPACE_LG   = dp(24)
    SPACE_XL   = dp(32)
    SPACE_2XL  = dp(48)
    SPACE_3XL  = dp(64)


# ═══════════════════════════════════════════════════════════════════════════════
#  BORDER RADIUS SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class Radius:
    """Slightly more rounded for friendlier feel."""
    NONE = 0
    SM   = dp(10)   # Slightly rounder than admin
    MD   = dp(14)
    LG   = dp(18)
    XL   = dp(28)
    FULL = dp(9999)

    RADIUS_SMALL  = dp(10)
    RADIUS_MEDIUM = dp(14)
    RADIUS_LARGE  = dp(18)
    RADIUS_XL     = dp(28)
    RADIUS_FULL   = dp(9999)


# ═══════════════════════════════════════════════════════════════════════════════
#  SHADOW / ELEVATION SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class Elevation:
    NONE   = 0
    LOW    = 2
    MEDIUM = 6
    HIGH   = 12
    XL     = 20

    SHADOW_COLOR = (0, 0, 0, 0.3)
    SHADOW_COLOR_DEEP = (0, 0, 0, 0.5)


# ═══════════════════════════════════════════════════════════════════════════════
#  ANIMATION DURATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class Animation:
    INSTANT  = 0.0
    FAST     = 0.15
    NORMAL   = 0.3
    SLOW     = 0.5
    GLACIAL  = 0.8

    EASE_IN = "in_cubic"
    EASE_OUT = "out_cubic"
    EASE_IN_OUT = "in_out_cubic"
    EASE_ELASTIC = "out_elastic"
    EASE_BOUNCE = "out_bounce"


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPONENT-SPECIFIC TOKENS
# ═══════════════════════════════════════════════════════════════════════════════

class ComponentTokens:
    """Component tokens — slightly rounder for client app."""

    # ── Navigation ────────────────────────────────────────────────────────
    NAV_BAR_HEIGHT = dp(64)
    NAV_BAR_PADDING_H = dp(20)

    # ── Cards ────────────────────────────────────────────────────────────
    CARD_PADDING = dp(20)
    CARD_SPACING = dp(12)
    CARD_BORDER_WIDTH = dp(1)
    CARD_BORDER_COLOR = get_color_from_hex("#2e2842")

    # ── Buttons ──────────────────────────────────────────────────────────
    BUTTON_HEIGHT = dp(48)
    BUTTON_HEIGHT_SM = dp(36)
    BUTTON_HEIGHT_LG = dp(56)
    BUTTON_RADIUS = dp(16)  # Rounder
    BUTTON_PADDING_H = dp(24)

    # ── Inputs ───────────────────────────────────────────────────────────
    INPUT_HEIGHT = dp(52)
    INPUT_RADIUS = dp(16)
    INPUT_PADDING_H = dp(16)

    # ── Badges ───────────────────────────────────────────────────────────
    BADGE_HEIGHT = dp(26)
    BADGE_RADIUS = dp(13)
    BADGE_PADDING_H = dp(12)

    # ── Avatars ──────────────────────────────────────────────────────────
    AVATAR_SIZE_SM = dp(32)
    AVATAR_SIZE_MD = dp(44)
    AVATAR_SIZE_LG = dp(64)

    # ── FAB ──────────────────────────────────────────────────────────────
    FAB_SIZE = dp(56)
    FAB_SIZE_MINI = dp(40)
    FAB_RADIUS = dp(18)

    # ── Modal ────────────────────────────────────────────────────────────
    MODAL_WIDTH = dp(420)
    MODAL_RADIUS = dp(24)
    MODAL_PADDING = dp(24)

    # ── Snackbar ─────────────────────────────────────────────────────────
    SNACKBAR_RADIUS = dp(14)
    SNACKBAR_PADDING = dp(16)
    SNACKBAR_MARGIN = dp(16)

    # ── Chat Bubbles ─────────────────────────────────────────────────────
    BUBBLE_RADIUS = dp(18)
    BUBBLE_PADDING_H = dp(14)
    BUBBLE_PADDING_V = dp(10)
    BUBBLE_MAX_WIDTH = 0.75  # % of parent width

    # ── Bottom Nav ───────────────────────────────────────────────────────
    BOTTOM_NAV_HEIGHT = dp(64)
    BOTTOM_NAV_RADIUS = dp(20)


# ═══════════════════════════════════════════════════════════════════════════════
#  LEGACY THEME CLASS (backward compatibility)
# ═══════════════════════════════════════════════════════════════════════════════

class Theme:
    """Legacy theme class for backward compatibility."""

    BG_BASE         = Colors.BG_BASE
    BG_CARD         = Colors.BG_CARD
    BG_INPUT        = Colors.BG_INPUT
    BG_HOVER        = Colors.BG_HOVER
    PRIMARY         = Colors.PRIMARY
    SECONDARY       = Colors.SECONDARY
    TEXT_PRIMARY    = Colors.TEXT_PRIMARY
    TEXT_SECONDARY  = Colors.TEXT_SECONDARY
    TEXT_HINT       = Colors.TEXT_HINT
    SUCCESS         = Colors.SUCCESS
    WARNING         = Colors.WARNING
    HIGHLIGHT       = Colors.HIGHLIGHT
    INFO            = Colors.INFO

    SPACE_XS   = Spacing.XS
    SPACE_SM   = Spacing.SM
    SPACE_MD   = Spacing.MD
    SPACE_LG   = Spacing.LG
    SPACE_XL   = Spacing.XL
    SPACE_2XL  = Spacing.XXL
    SPACE_3XL  = Spacing.XXXL

    RADIUS_SMALL  = Radius.SM
    RADIUS_MEDIUM = Radius.MD
    RADIUS_LARGE  = Radius.LG
    RADIUS_XL     = Radius.XL
    RADIUS_FULL   = Radius.FULL

    ELEVATION_NONE  = Elevation.NONE
    ELEVATION_LOW   = Elevation.LOW
    ELEVATION_MED   = Elevation.MEDIUM
    ELEVATION_HIGH  = Elevation.HIGH

    ANIM_FAST   = Animation.FAST
    ANIM_NORMAL = Animation.NORMAL
    ANIM_SLOW   = Animation.SLOW


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> tuple:
    """Convert hex color string to RGBA tuple with optional alpha."""
    return (*get_color_from_hex(hex_color)[:3], alpha)


def lighten(color: tuple, amount: float = 0.1) -> tuple:
    """Lighten an RGBA color by a given amount (0-1)."""
    r, g, b, a = color[:4]
    return (min(1.0, r + amount), min(1.0, g + amount), min(1.0, b + amount), a)


def darken(color: tuple, amount: float = 0.1) -> tuple:
    """Darken an RGBA color by a given amount (0-1)."""
    r, g, b, a = color[:4]
    return (max(0.0, r - amount), max(0.0, g - amount), max(0.0, b - amount), a)


def with_alpha(color: tuple, alpha: float) -> tuple:
    """Return the color with a new alpha value."""
    return (*color[:3], alpha)
