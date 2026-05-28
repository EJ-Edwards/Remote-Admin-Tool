from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Agent, Alert, AuditEvent, System, User
from app.schemas import DashboardSummary
from app.services.risk_scoring import SENSITIVE_CATEGORIES

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = user.workspace_id
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return DashboardSummary(
        total_systems=db.query(func.count(System.id)).filter(System.workspace_id == ws).scalar() or 0,
        active_agents=db.query(func.count(Agent.id)).filter(
            Agent.workspace_id == ws, Agent.status == "approved"
        ).scalar() or 0,
        access_events_today=db.query(func.count(AuditEvent.id)).filter(
            AuditEvent.workspace_id == ws, AuditEvent.occurred_at >= today_start
        ).scalar() or 0,
        sensitive_downloads=db.query(func.count(AuditEvent.id)).filter(
            AuditEvent.workspace_id == ws,
            AuditEvent.event_type == "file.downloaded",
            AuditEvent.resource_category.in_(list(SENSITIVE_CATEGORIES)),
        ).scalar() or 0,
        failed_access_attempts=db.query(func.count(AuditEvent.id)).filter(
            AuditEvent.workspace_id == ws, AuditEvent.event_type == "user.login_failed"
        ).scalar() or 0,
        open_alerts=db.query(func.count(Alert.id)).filter(
            Alert.workspace_id == ws, Alert.status == "open"
        ).scalar() or 0,
    )
