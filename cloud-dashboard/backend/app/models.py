import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    plan: Mapped[str] = mapped_column(String(50), default="starter")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    users: Mapped[list["User"]] = relationship(back_populates="workspace")
    systems: Mapped[list["System"]] = relationship(back_populates="workspace")
    agents: Mapped[list["Agent"]] = relationship(back_populates="workspace")


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="owner")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    workspace: Mapped["Workspace"] = relationship(back_populates="users")


class System(Base):
    __tablename__ = "systems"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="server")
    status: Mapped[str] = mapped_column(String(50), default="active")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    workspace: Mapped["Workspace"] = relationship(back_populates="systems")
    agents: Mapped[list["Agent"]] = relationship(back_populates="system")


class AgentEnrollmentToken(Base):
    __tablename__ = "agent_enrollment_tokens"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="default")
    status: Mapped[str] = mapped_column(String(50), default="active")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    system_id: Mapped[str] = mapped_column(ForeignKey("systems.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    version: Mapped[str] = mapped_column(String(50), default="0.1.0")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    workspace: Mapped["Workspace"] = relationship(back_populates="agents")
    system: Mapped["System"] = relationship(back_populates="agents")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    system_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    resource_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    result: Mapped[str] = mapped_column(String(50), default="success")
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(50), default="low")
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    audit_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), default="medium")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), default="csv")
    date_range_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    date_range_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    download_url: Mapped[str | None] = mapped_column(String(512), nullable=True)


class WorkspaceSettings(Base):
    __tablename__ = "workspace_settings"
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id"), primary_key=True)
    alert_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sensitive_categories: Mapped[str] = mapped_column(
        Text, default="customer_data,financial_data,private_report,sensitive"
    )
