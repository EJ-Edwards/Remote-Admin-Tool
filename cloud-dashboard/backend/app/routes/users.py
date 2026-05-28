from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(User).filter(User.workspace_id == user.workspace_id).all()
