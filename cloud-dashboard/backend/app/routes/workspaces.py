from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User, Workspace
from app.schemas import WorkspaceOut

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceOut])
def list_workspaces(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == user.workspace_id).all()
    return ws


@router.post("", response_model=WorkspaceOut)
def create_workspace(
    name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = Workspace(name=name, owner_id=user.id)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


@router.get("/{workspace_id}", response_model=WorkspaceOut)
def get_workspace(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if workspace_id != user.workspace_id:
        raise HTTPException(403, "Access denied")
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
    return ws
