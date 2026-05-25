"""
Flora Admin Panel — Screen registry & imports.
"""
from app_admin.screens.login_screen import LoginScreen
from app_admin.screens.dashboard_screen import DashboardScreen
from app_admin.screens.bots_screen import BotsScreen
from app_admin.screens.bot_create_screen import BotCreateScreen
from app_admin.screens.licenses_screen import LicensesScreen
from app_admin.screens.users_screen import UsersScreen
from app_admin.screens.plans_screen import PlansScreen
from app_admin.screens.analytics_screen import AnalyticsScreen
from app_admin.screens.settings_screen import SettingsScreen

__all__ = [
    "LoginScreen",
    "DashboardScreen",
    "BotsScreen",
    "BotCreateScreen",
    "LicensesScreen",
    "UsersScreen",
    "PlansScreen",
    "AnalyticsScreen",
    "SettingsScreen",
]
