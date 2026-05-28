from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Alert, User
from app.schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Alert)
        .filter(Alert.workspace_id == user.workspace_id)
        .order_by(Alert.created_at.desc())
        .limit(200)
        .all()
    )


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.workspace_id == user.workspace_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    return alert


@router.patch("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.workspace_id == user.workspace_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.status = "acknowledged"
    alert.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.workspace_id == user.workspace_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.status = "resolved"
    alert.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert
