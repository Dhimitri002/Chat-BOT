"""
Flora Platform — Schemas
"""
from backend.schemas.common import (
    ResponseBase, ErrorResponse, PaginatedResponse,
    MessageResponse, SuccessResponse,
)
from backend.schemas.auth import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    RefreshToken, TwoFactorSetup, TwoFactorVerify, PasswordReset,
)
from backend.schemas.user import (
    UserUpdate, UserProfile, ChangePassword,
)
from backend.schemas.bot import (
    BotCreate, BotUpdate, BotResponse, BotStats,
)
from backend.schemas.license import (
    LicenseCreate, LicenseValidate, LicenseResponse,
    LicenseValidationResponse, LicenseRevoke, LicenseRenew,
)
from backend.schemas.plan import (
    PlanCreate, PlanUpdate, PlanResponse, PlanComparison,
)
from backend.schemas.subscription import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionCancel,
    SubscriptionResponse, SubscriptionWithPlan,
)
from backend.schemas.whatsapp import (
    WhatsAppConnect, WhatsAppDisconnect, WhatsAppSendMessage,
    WhatsAppSendMedia, QRCodeResponse, SessionStatusResponse,
    SessionListResponse, WhatsAppWebhook,
)
from backend.schemas.intent import (
    IntentCreate, IntentUpdate, IntentResponse, IntentTest, IntentTestResult,
)
from backend.schemas.command import (
    CommandCreate, CommandUpdate, CommandResponse, CommandTest, CommandTestResult,
)
from backend.schemas.chat import (
    ChatMessage, ChatHistoryRequest, ChatHistoryItem,
    ChatHistoryResponse, ChatConversationsRequest, ChatConversation,
)
from backend.schemas.analytics import (
    DateRange, BotAnalytics, BotStatsResponse, AdminDashboardStats,
    LLMUsageStats, LLMUsageResponse,
)
from backend.schemas.system import (
    HealthCheck, SystemConfig, SystemConfigUpdate,
    SystemEventResponse, AuditLogResponse,
    BackupCreate, BackupResponse, BackupRestore,
)

__all__ = [
    # Common
    "ResponseBase", "ErrorResponse", "PaginatedResponse",
    # Auth
    "UserCreate", "UserLogin", "UserResponse", "TokenResponse",
    # User
    "UserUpdate", "UserProfile", "ChangePassword",
    # Bot
    "BotCreate", "BotUpdate", "BotResponse", "BotStats",
    # License
    "LicenseCreate", "LicenseValidate", "LicenseResponse", "LicenseValidationResponse",
    # Plan
    "PlanCreate", "PlanUpdate", "PlanResponse",
    # Subscription
    "SubscriptionCreate", "SubscriptionResponse",
    # WhatsApp
    "WhatsAppConnect", "WhatsAppDisconnect", "WhatsAppSendMessage",
    "QRCodeResponse", "SessionStatusResponse",
    # Intent
    "IntentCreate", "IntentUpdate", "IntentResponse",
    # Command
    "CommandCreate", "CommandUpdate", "CommandResponse",
    # Chat
    "ChatMessage", "ChatHistoryResponse",
    # Analytics
    "BotStatsResponse", "AdminDashboardStats", "LLMUsageResponse",
    # System
    "HealthCheck", "SystemConfig", "BackupResponse",
]
