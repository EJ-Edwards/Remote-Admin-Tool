from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User, WorkspaceSettings
from app.schemas import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.query(WorkspaceSettings).filter(WorkspaceSettings.workspace_id == user.workspace_id).first()
    if not s:
        s = WorkspaceSettings(workspace_id=user.workspace_id)
        db.add(s)
        db.commit()
        db.refresh(s)
    return SettingsOut(
        workspace_id=s.workspace_id,
        alert_email=s.alert_email,
        sensitive_categories=s.sensitive_categories,
    )


@router.patch("", response_model=SettingsOut)
def update_settings(
    body: SettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = db.query(WorkspaceSettings).filter(WorkspaceSettings.workspace_id == user.workspace_id).first()
    if not s:
        raise HTTPException(404, "Settings not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return SettingsOut(
        workspace_id=s.workspace_id,
        alert_email=s.alert_email,
        sensitive_categories=s.sensitive_categories,
    )
