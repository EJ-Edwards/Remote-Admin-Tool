"""Evaluate alert rules after audit event ingestion."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Alert, AuditEvent
from app.services.risk_scoring import SENSITIVE_CATEGORIES


def evaluate_alerts(db: Session, event: AuditEvent) -> list[Alert]:
    created: list[Alert] = []
    ws = event.workspace_id

    if event.event_type == "file.downloaded" and event.resource_category in SENSITIVE_CATEGORIES:
        created.append(_alert(
            ws, event.id, "high",
            "Sensitive download detected",
            f"{event.user_email or 'Unknown user'} downloaded {event.resource_name or 'a file'}",
        ))

    if event.user_email and event.ip_address:
        prior = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.workspace_id == ws,
                AuditEvent.user_email == event.user_email,
                AuditEvent.ip_address == event.ip_address,
                AuditEvent.id != event.id,
            )
            .first()
        )
        if not prior and event.event_type not in ("system.heartbeat",):
            created.append(_alert(
                ws, event.id, "medium",
                "New IP address detected",
                f"{event.user_email} from {event.ip_address}",
            ))

    if event.event_type == "user.login_failed":
        window = datetime.now(timezone.utc) - timedelta(minutes=10)
        q = db.query(func.count(AuditEvent.id)).filter(
            AuditEvent.workspace_id == ws,
            AuditEvent.event_type == "user.login_failed",
            AuditEvent.occurred_at >= window,
        )
        if event.user_email:
            count = q.filter(AuditEvent.user_email == event.user_email).scalar() or 0
        elif event.ip_address:
            count = q.filter(AuditEvent.ip_address == event.ip_address).scalar() or 0
        else:
            count = q.scalar() or 0
        if count >= 5:
            created.append(_alert(
                ws, event.id, "high",
                "Failed login spike",
                "More than 5 failed logins in 10 minutes",
            ))

    if event.event_type == "role.changed":
        created.append(_alert(
            ws, event.id, "high",
            "Role change detected",
            f"Role changed for {event.user_email or 'a user'}",
        ))

    for alert in created:
        db.add(alert)
    if created:
        db.commit()
    return created


def _alert(workspace_id: str, audit_event_id: str, severity: str, title: str, description: str) -> Alert:
    return Alert(
        workspace_id=workspace_id,
        audit_event_id=audit_event_id,
        severity=severity,
        title=title,
        description=description,
        status="open",
    )


def check_offline_systems(db: Session, workspace_id: str, offline_minutes: int) -> list[Alert]:
    from app.models import Agent, System
    threshold = datetime.now(timezone.utc) - timedelta(minutes=offline_minutes)
    created = []
    agents = db.query(Agent).filter(Agent.workspace_id == workspace_id, Agent.status == "approved").all()
    for agent in agents:
        if agent.last_seen_at and agent.last_seen_at >= threshold:
            continue
        sys = db.query(System).filter(System.id == agent.system_id).first()
        if sys and sys.status != "offline":
            sys.status = "offline"
            created.append(_alert(
                workspace_id, None, "medium",
                "System offline",
                f"{sys.name} has not sent a heartbeat recently",
            ))
    if created:
        db.commit()
    return created
