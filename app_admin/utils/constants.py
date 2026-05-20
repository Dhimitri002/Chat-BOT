"""
Constants for the Flora Admin Panel.
"""

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
API_TIMEOUT = 30

# Auth endpoints
API_LOGIN = f"{API_PREFIX}/auth/login"
API_LOGOUT = f"{API_PREFIX}/auth/logout"
API_ME = f"{API_PREFIX}/auth/me"
API_REFRESH = f"{API_PREFIX}/auth/refresh"

# Admin endpoints
API_ADMIN_DASHBOARD = f"{API_PREFIX}/admin/dashboard"
API_ADMIN_USERS = f"{API_PREFIX}/admin/users"
API_ADMIN_BOTS = f"{API_PREFIX}/admin/bots"
API_ADMIN_LICENSES = f"{API_PREFIX}/admin/licenses"
API_ADMIN_SETTINGS = f"{API_PREFIX}/admin/settings"
API_ADMIN_BROADCAST = f"{API_PREFIX}/admin/broadcast"

# Plans endpoints
API_PLANS = f"{API_PREFIX}/plans"

# Analytics endpoints
API_ANALYTICS = f"{API_PREFIX}/analytics"

# Theme Colors - Dark Premium (Deep Purple/Indigo)
class Colors:
    """Color palette for the admin panel."""
    # Primary
    PRIMARY = (0.361, 0.208, 0.694, 1)        # Deep Purple #5C34B1
    PRIMARY_DARK = (0.255, 0.141, 0.525, 1)    # Darker Purple #412486
    PRIMARY_LIGHT = (0.478, 0.337, 0.812, 1)   # Lighter Purple #7A56CF
    PRIMARY_ACCENT = (0.545, 0.271, 0.678, 1)  # Accent Purple #8B46AD

    # Secondary / Accent
    SECONDARY = (0.129, 0.588, 0.953, 1)       # Blue #2196F3
    ACCENT = (0.012, 0.663, 0.957, 1)          # Light Blue #03A9F4
    TEAL = (0.0, 0.737, 0.831, 1)              # Teal #00BCD4

    # Background
    BG_DARK = (0.082, 0.082, 0.114, 1)         # #15151D
    BG_CARD = (0.118, 0.118, 0.161, 1)         # #1E1E29
    BG_SURFACE = (0.145, 0.145, 0.192, 1)      # #252530
    BG_HOVER = (0.176, 0.176, 0.227, 1)        # #2D2D3A
    BG_INPUT = (0.102, 0.102, 0.141, 1)        # #1A1A24

    # Text
    TEXT_PRIMARY = (1, 1, 1, 1)                # White
    TEXT_SECONDARY = (0.702, 0.702, 0.78, 1)   # #B3B3C7
    TEXT_HINT = (0.471, 0.471, 0.588, 1)       # #787896
    TEXT_DISABLED = (0.314, 0.314, 0.412, 1)   # #505069

    # Status
    SUCCESS = (0.298, 0.686, 0.314, 1)         # Green #4CAF50
    WARNING = (1.0, 0.757, 0.027, 1)           # Amber #FFC107
    ERROR = (0.957, 0.263, 0.212, 1)           # Red #F44336
    INFO = (0.129, 0.588, 0.953, 1)            # Blue #2196F3

    # Bot Status
    BOT_ONLINE = (0.298, 0.686, 0.314, 1)      # Green
    BOT_OFFLINE = (0.471, 0.471, 0.588, 1)     # Gray
    BOT_PAUSED = (1.0, 0.757, 0.027, 1)        # Amber
    BOT_ERROR = (0.957, 0.263, 0.212, 1)       # Red

    # Overlay
    OVERLAY = (0, 0, 0, 0.6)
    DIVIDER = (0.176, 0.176, 0.227, 1)

    # Chart colors
    CHART_COLORS = [
        (0.361, 0.208, 0.694, 1),   # Purple
        (0.129, 0.588, 0.953, 1),   # Blue
        (0.012, 0.663, 0.957, 1),   # Light Blue
        (0.0, 0.737, 0.831, 1),     # Teal
        (0.298, 0.686, 0.314, 1),   # Green
        (1.0, 0.757, 0.027, 1),     # Amber
        (0.957, 0.263, 0.212, 1),   # Red
    ]


# Navigation items
NAV_ITEMS = [
    {"name": "dashboard", "icon": "view-dashboard", "label": "Painel"},
    {"name": "users", "icon": "account-group", "label": "Usuarios"},
    {"name": "bots", "icon": "robot", "label": "Bots"},
    {"name": "plans", "icon": "package-variant", "label": "Planos"},
    {"name": "licenses", "icon": "key-variant", "label": "Licencas"},
    {"name": "analytics", "icon": "chart-line", "label": "Analises"},
    {"name": "settings", "icon": "cog", "label": "Configuracoes"},
]

# Bot status labels (Portuguese)
BOT_STATUS_LABELS = {
    "connected": "Conectado",
    "disconnected": "Desconectado",
    "paused": "Pausado",
    "error": "Erro",
}

# User role labels
ROLE_LABELS = {
    "user": "Usuario",
    "admin": "Admin",
    "superadmin": "Super Admin",
}

# License status labels
LICENSE_STATUS_LABELS = {
    "active": "Ativa",
    "expired": "Expirada",
    "revoked": "Revogada",
    "pending": "Pendente",
}

# Pagination
ITEMS_PER_PAGE = 20

# Date formats
DATE_FORMAT = "%d/%m/%Y"
DATETIME_FORMAT = "%d/%m/%Y %H:%M"
