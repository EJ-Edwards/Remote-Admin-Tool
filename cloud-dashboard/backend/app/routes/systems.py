from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import System, User
from app.schemas import SystemCreate, SystemOut, SystemUpdate

router = APIRouter(prefix="/systems", tags=["systems"])


@router.get("", response_model=list[SystemOut])
def list_systems(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(System).filter(System.workspace_id == user.workspace_id).all()


@router.post("", response_model=SystemOut)
def create_system(
    body: SystemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sys = System(workspace_id=user.workspace_id, name=body.name, type=body.type)
    db.add(sys)
    db.commit()
    db.refresh(sys)
    return sys


@router.get("/{system_id}", response_model=SystemOut)
def get_system(
    system_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sys = db.query(System).filter(System.id == system_id, System.workspace_id == user.workspace_id).first()
    if not sys:
        raise HTTPException(404, "System not found")
    return sys


@router.patch("/{system_id}", response_model=SystemOut)
def update_system(
    system_id: str,
    body: SystemUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sys = db.query(System).filter(System.id == system_id, System.workspace_id == user.workspace_id).first()
    if not sys:
        raise HTTPException(404, "System not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(sys, k, v)
    db.commit()
    db.refresh(sys)
    return sys


@router.delete("/{system_id}")
def delete_system(
    system_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sys = db.query(System).filter(System.id == system_id, System.workspace_id == user.workspace_id).first()
    if not sys:
        raise HTTPException(404, "System not found")
    db.delete(sys)
    db.commit()
    return {"status": "deleted"}
