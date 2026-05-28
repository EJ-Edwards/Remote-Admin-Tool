"""Audit event models — metadata only."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from utils.privacy import assert_safe_metadata, FORBIDDEN_TOP_LEVEL_KEYS


class EventType(str, Enum):
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"
    RESOURCE_VIEWED = "resource.viewed"
    FILE_DOWNLOADED = "file.downloaded"
    REPORT_EXPORTED = "report.exported"
    ROLE_CHANGED = "role.changed"
    MEMBER_INVITED = "member.invited"
    MEMBER_REMOVED = "member.removed"
    SYSTEM_HEARTBEAT = "system.heartbeat"
    SYSTEM_OFFLINE = "system.offline"
    NEW_IP_DETECTED = "new_ip.detected"
    SENSITIVE_DOWNLOAD_DETECTED = "sensitive_download.detected"
    FAILED_ACCESS_SPIKE_DETECTED = "failed_access_spike.detected"
    UNUSUAL_ACCESS_DETECTED = "unusual_access.detected"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    event_type: EventType
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
    risk_level: RiskLevel = RiskLevel.LOW
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: dict[str, Any]) -> dict[str, Any]:
        assert_safe_metadata(v)
        return v

    def model_post_init(self, __context: Any) -> None:
        for key in FORBIDDEN_TOP_LEVEL_KEYS:
            if getattr(self, key, None) is not None:
                raise ValueError(f"Forbidden field: {key}")

    def to_api_dict(self) -> dict[str, Any]:
        d = self.model_dump(mode="json")
        if d.get("timestamp") and not isinstance(d["timestamp"], str):
            d["timestamp"] = self.timestamp.isoformat().replace("+00:00", "Z")
        d["event_type"] = self.event_type.value
        d["risk_level"] = self.risk_level.value
        return d
