"""
Helper functions for the Flora Admin Panel.
"""
from datetime import datetime, timezone


def format_currency(value: float, currency: str = "BRL") -> str:
    """Format a value as currency."""
    if currency == "BRL":
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{currency} {value:,.2f}"


def format_number(value: int) -> str:
    """Format a large number with suffixes."""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def format_datetime(dt: str | datetime | None) -> str:
    """Format a datetime string or object to readable format."""
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return str(dt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%d/%m/%Y %H:%M")


def format_date(dt: str | datetime | None) -> str:
    """Format a datetime to date only."""
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return str(dt)
    return dt.strftime("%d/%m/%Y")


def time_ago(dt: str | datetime | None) -> str:
    """Return a human-readable 'time ago' string."""
    if dt is None:
        return "Nunca"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return str(dt)
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "Agora mesmo"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min atras"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h atras"
    days = hours // 24
    if days < 30:
        return f"{days}d atras"
    months = days // 30
    if months < 12:
        return f"{months} mes(es) atras"
    years = months // 12
    return f"{years} ano(s) atras"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def get_status_color(status: str, status_map: dict) -> tuple:
    """Get color for a status value."""
    from app_admin.utils.constants import Colors

    color_map = {
        "connected": Colors.BOT_ONLINE,
        "active": Colors.SUCCESS,
        "online": Colors.SUCCESS,
        "disconnected": Colors.BOT_OFFLINE,
        "inactive": Colors.BOT_OFFLINE,
        "paused": Colors.BOT_PAUSED,
        "pending": Colors.WARNING,
        "error": Colors.BOT_ERROR,
        "expired": Colors.ERROR,
        "revoked": Colors.ERROR,
        "banned": Colors.ERROR,
    }
    return color_map.get(status.lower(), Colors.TEXT_SECONDARY)


def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    if len(password) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres"
    return True, ""


def generate_license_key() -> str:
    """Generate a random license key."""
    import uuid
    import base64
    uid = uuid.uuid4().bytes + uuid.uuid4().bytes[:4]
    key = base64.b32encode(uid).decode("utf-8")[:20]
    return f"FLORA-{key[:4]}-{key[4:8]}-{key[8:12]}-{key[12:16]}"


def format_percentage(value: float, total: float) -> str:
    """Format a value as percentage of total."""
    if total == 0:
        return "0%"
    pct = (value / total) * 100
    return f"{pct:.1f}%"


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human readable."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
