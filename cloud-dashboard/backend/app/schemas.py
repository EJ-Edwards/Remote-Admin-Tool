from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    workspace_name: str = "My Workspace"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    workspace_id: str
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True


class WorkspaceOut(BaseModel):
    id: str
    name: str
    plan: str
    created_at: datetime

    class Config:
        from_attributes = True


class EnrollmentTokenCreate(BaseModel):
    name: str = "default"


class EnrollmentTokenOut(BaseModel):
    id: str
    token: str
    name: str
    status: str
    expires_at: Optional[datetime] = None


class AgentEnrollRequest(BaseModel):
    enrollment_token: str
    system_name: str


class AgentEnrollResponse(BaseModel):
    agent_id: str
    workspace_id: str
    system_id: str
    agent_token: str


class AgentOut(BaseModel):
    id: str
    workspace_id: str
    system_id: str
    agent_name: str
    status: str
    version: str
    last_seen_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemCreate(BaseModel):
    name: str
    type: str = "server"


class SystemUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None


class SystemOut(BaseModel):
    id: str
    workspace_id: str
    name: str
    type: str
    status: str
    last_seen_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditEventIn(BaseModel):
    event_id: str
    event_type: str
    workspace_id: Optional[str] = None
    system_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_email: Optional[str] = None
    resource_name: Optional[str] = None
    resource_type: Optional[str] = None
    resource_category: Optional[str] = None
    result: str = "success"
    ip_address: Optional[str] = None
    device_name: Optional[str] = None
    risk_level: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class EventsBatchIn(BaseModel):
    events: list[AuditEventIn]


class EventsBatchOut(BaseModel):
    accepted_event_ids: list[str]
    count: int


class HeartbeatIn(BaseModel):
    agent_id: str
    system_id: str
    device_name: Optional[str] = None


class AuditEventOut(BaseModel):
    id: str
    event_id: str
    event_type: str
    user_email: Optional[str] = None
    resource_name: Optional[str] = None
    resource_category: Optional[str] = None
    result: str
    ip_address: Optional[str] = None
    risk_level: str
    occurred_at: datetime

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: str
    severity: str
    title: str
    description: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReportCreate(BaseModel):
    title: str
    report_type: str = "csv"
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None


class ReportOut(BaseModel):
    id: str
    title: str
    report_type: str
    download_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SettingsOut(BaseModel):
    workspace_id: str
    alert_email: Optional[str] = None
    sensitive_categories: str


class SettingsUpdate(BaseModel):
    alert_email: Optional[str] = None
    sensitive_categories: Optional[str] = None


class DashboardSummary(BaseModel):
    total_systems: int
    active_agents: int
    access_events_today: int
    sensitive_downloads: int
    failed_access_attempts: int
    open_alerts: int
