"""
Theme — Shared design tokens for the Flora Admin Panel.

Dark premium palette:
  BG_BASE      #0f0f1a  (deepest background)
  BG_SURFACE   #16213e  (sidebar / panels)
  BG_CARD      #1a1a2e  (card surfaces)
  BG_INPUT     #1e2a4a  (input fields)
  PRIMARY      #4ecca3  (accent green)
  HIGHLIGHT    #e94560  (red highlight / danger)
  TEXT_PRIMARY #ffffff
  TEXT_SECONDARY #a0aec0
  TEXT_HINT    #5a6a8a
"""

from kivy.metrics import dp


class Colors:
    """Colour tokens."""
    BG_BASE        = (0.059, 0.059, 0.102, 1)   # #0f0f1a
    BG_SURFACE     = (0.086, 0.129, 0.243, 1)    # #16213e
    BG_CARD        = (0.102, 0.102, 0.180, 1)    # #1a1a2e
    BG_INPUT       = (0.118, 0.165, 0.290, 1)    # #1e2a4a
    BG_HOVER       = (0.141, 0.192, 0.337, 1)    # #243156

    PRIMARY_DARK   = (0.220, 0.620, 0.502, 1)    # #329e80
    PRIMARY        = (0.306, 0.800, 0.639, 1)    # #4ecca3
    PRIMARY_LIGHT  = [c * 1.3 for c in (0.306, 0.800, 0.639, 1)][:3] + [1]

    HIGHLIGHT      = (0.914, 0.271, 0.376, 1)    # #e94560
    WARNING        = (0.957, 0.682, 0.161, 1)    # #f4ae29
    INFO           = (0.243, 0.588, 0.871, 1)    # #3ea4de
    SUCCESS        = (0.306, 0.800, 0.639, 1)    # #4ecca3

    TEXT_PRIMARY   = (1, 1, 1, 1)                # #ffffff
    TEXT_SECONDARY = (0.627, 0.675, 0.753, 1)    # #a0aec0
    TEXT_HINT      = (0.353, 0.416, 0.541, 1)    # #5a6a8a

    ERROR          = (0.914, 0.271, 0.376, 1)    # #e94560
    WHITE          = (1, 1, 1, 1)
    TRANSPARENT    = (0, 0, 0, 0)


class Theme:
    """Spacing, sizing, elevation & animation constants."""

    # ── Spacing ────────────────────────────────────────────
    SPACE_XS  = dp(4)
    SPACE_SM  = dp(8)
    SPACE_MD  = dp(12)
    SPACE_LG  = dp(16)
    SPACE_XL  = dp(24)
    SPACE_2XL = dp(32)

    # ── Radii ─────────────────────────────────────────────
    RADIUS_XS    = dp(4)
    RADIUS_SM    = dp(8)
    RADIUS_MEDIUM = dp(12)
    RADIUS_LARGE  = dp(16)
    RADIUS_XL     = dp(20)
    RADIUS_2XL    = dp(24)

    # ── Elevations ────────────────────────────────────────
    ELEVATION_NONE   = 0
    ELEVATION_LOW    = 2
    ELEVATION_MEDIUM = 6
    ELEVATION_HIGH   = 10
    ELEVATION_MODAL  = 16

    # ── Fixed heights ─────────────────────────────────────
    TOP_BAR_HEIGHT   = dp(56)
    SIDEBAR_WIDTH    = dp(240)
    SIDEBAR_COLLAPSED = dp(56)

    # ── Animation durations (seconds) ─────────────────────
    ANIM_FAST   = 0.15
    ANIM_MEDIUM = 0.25
    ANIM_SLOW   = 0.4

    # ── Opacities ────────────────────────────────────────
    OPACITY_DISABLED = 0.38
    OPACITY_OVERLAY  = 0.6
