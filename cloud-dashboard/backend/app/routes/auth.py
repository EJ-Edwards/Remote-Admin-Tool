from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models import User, Workspace, WorkspaceSettings
from app.schemas import LoginRequest, SignupRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(400, "Email already registered")
    ws = Workspace(name=body.workspace_name)
    db.add(ws)
    db.flush()
    user = User(
        workspace_id=ws.id,
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role="owner",
    )
    ws.owner_id = user.id
    db.add(user)
    db.add(WorkspaceSettings(workspace_id=ws.id))
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/logout")
def logout():
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
