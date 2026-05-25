"""
Constants — API endpoints, default values & shared helpers for the Flora Admin Panel.
"""

from app_admin.styles.theme import Colors

# ── Base URL ────────────────────────────────────────────────────────────
# Make sure this matches your backend address in development.
BASE_URL = "http://localhost:8000/api/v1"

# ── API Endpoints ───────────────────────────────────────────────────────
class API:
    # Auth
    LOGIN          = "/auth/login"
    REGISTER       = "/auth/register"
    REFRESH        = "/auth/refresh"
    LOGOUT         = "/auth/logout"

    # Admin Dashboard
    ADMIN_DASHBOARD = "/admin/dashboard"

    # Admin — Users
    ADMIN_USERS      = "/admin/users"
    ADMIN_USER       = "/admin/users/{user_id}"

    # Admin — Bots
    ADMIN_BOTS       = "/admin/bots"

    # Admin — Licenses
    ADMIN_LICENSES   = "/admin/licenses"

    # Admin — Events & Audit
    ADMIN_EVENTS     = "/admin/events"
    AUDIT_LOGS       = "/admin/audit-logs"

    # Plans (client-facing)
    PLANS            = "/plans"

    # Analytics
    ANALYTICS_DASHBOARD  = "/analytics/dashboard"
    ANALYTICS_LLM_USAGE  = "/analytics/llm-usage"
    ANALYTICS_REVENUE    = "/analytics/revenue"
    ANALYTICS_USERS      = "/analytics/users"
    ANALYTICS_MESSAGES   = "/analytics/messages"

# ── Pagination defaults ────────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE     = 100

# ── Status display labels ───────────────────────────────────────────────
STATUS_LABELS = {
    "active":    "Ativo",
    "inactive":  "Inativo",
    "pending":   "Pendente",
    "expired":   "Expirado",
    "revoked":   "Revogado",
    "connected": "Conectado",
    "disconnected": "Desconectado",
    "error":     "Erro",
}

ROLE_LABELS = {
    "admin":  "Administrador",
    "user":   "Usuário",
    "client": "Cliente",
}

# ── Status colour mapping ───────────────────────────────────────────────
STATUS_COLORS = {
    "active":      Colors.SUCCESS,
    "connected":   Colors.SUCCESS,
    "inactive":    Colors.TEXT_HINT,
    "pending":     Colors.WARNING,
    "expired":     Colors.HIGHLIGHT,
    "revoked":     Colors.HIGHLIGHT,
    "error":       Colors.HIGHLIGHT,
    "disconnected": Colors.TEXT_HINT,
}


def display_status(status: str) -> str:
    return STATUS_LABELS.get(status, status.capitalize())


def status_color(status: str):
    return STATUS_COLORS.get(status, Colors.TEXT_SECONDARY)


def display_role(role: str) -> str:
    return ROLE_LABELS.get(role, role.capitalize())
