"""
Flora Platform — System Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HealthCheck(BaseModel):
    status: str
    version: str
    database: str
    uptime_seconds: float
    timestamp: datetime


class SystemConfig(BaseModel):
    maintenance_mode: bool = False
    registration_enabled: bool = True
    trial_enabled: bool = True
    trial_days: int = 7
    max_upload_size_mb: int = 10
    default_language: str = "pt-BR"
    support_email: str = ""


class SystemConfigUpdate(BaseModel):
    maintenance_mode: Optional[bool] = None
    registration_enabled: Optional[bool] = None
    trial_enabled: Optional[bool] = None
    trial_days: Optional[int] = None
    max_upload_size_mb: Optional[int] = None
    default_language: Optional[str] = None
    support_email: Optional[str] = None


class SystemEventResponse(BaseModel):
    id: str
    event_type: str
    severity: str
    message: str
    details: Dict[str, Any]
    source: str
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str]
    action: str
    entity_type: str
    entity_id: str
    details: Dict[str, Any]
    ip_address: str
    created_at: datetime

    class Config:
        from_attributes = True


class BackupCreate(BaseModel):
    name: str = ""
    include_database: bool = True
    include_configs: bool = True


class BackupResponse(BaseModel):
    id: str
    name: str
    size_bytes: int
    status: str
    created_at: datetime
    created_by: str

    class Config:
        from_attributes = True


class BackupRestore(BaseModel):
    backup_id: str
    confirm: bool = False
