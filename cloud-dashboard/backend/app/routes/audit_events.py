import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Agent, AuditEvent, User
from app.schemas import AuditEventIn, AuditEventOut
from app.services.alert_rules import evaluate_alerts
from app.services.risk_scoring import default_risk_level

router = APIRouter(prefix="/audit-events", tags=["audit-events"])

FORBIDDEN = frozenset({
    "password", "file_content", "keystrokes", "screenshot", "clipboard", "token",
})


def _validate_event(data: AuditEventIn) -> None:
    meta = data.metadata or {}
    for key in meta:
        if key.lower() in FORBIDDEN:
            raise HTTPException(422, f"Forbidden metadata key: {key}")


def ingest_events(db: Session, agent: Agent, events: list[AuditEventIn]) -> list[str]:
    accepted = []
    for data in events:
        _validate_event(data)
        existing = db.query(AuditEvent).filter(AuditEvent.event_id == data.event_id).first()
        if existing:
            accepted.append(data.event_id)
            continue
        risk = default_risk_level(data.event_type, data.resource_category, data.risk_level)
        row = AuditEvent(
            event_id=data.event_id,
            workspace_id=agent.workspace_id,
            system_id=data.system_id or agent.system_id,
            agent_id=data.agent_id or agent.id,
            user_email=data.user_email,
            event_type=data.event_type,
            action=data.event_type,
            resource_type=data.resource_type,
            resource_name=data.resource_name,
            resource_category=data.resource_category,
            result=data.result,
            ip_address=data.ip_address,
            device_name=data.device_name,
            risk_level=risk,
            metadata_json=json.dumps(data.metadata) if data.metadata else None,
            occurred_at=data.timestamp,
        )
        db.add(row)
        db.flush()
        evaluate_alerts(db, row)
        accepted.append(data.event_id)
    db.commit()
    return accepted


@router.get("", response_model=list[AuditEventOut])
def list_events(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(AuditEvent)
        .filter(AuditEvent.workspace_id == user.workspace_id)
        .order_by(AuditEvent.occurred_at.desc())
        .limit(500)
        .all()
    )
    return rows


@router.get("/export")
def export_events(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.reports import export_audit_events_csv
    csv_data = export_audit_events_csv(db, user.workspace_id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit-events.csv"},
    )


@router.get("/{event_id}", response_model=AuditEventOut)
def get_event(
    event_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(AuditEvent)
        .filter(AuditEvent.workspace_id == user.workspace_id, AuditEvent.event_id == event_id)
        .first()
    )
    if not row:
        row = (
            db.query(AuditEvent)
            .filter(AuditEvent.workspace_id == user.workspace_id, AuditEvent.id == event_id)
            .first()
        )
    if not row:
        raise HTTPException(404, "Event not found")
    return row
