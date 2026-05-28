from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Agent, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)
agent_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def get_current_agent(
    creds: HTTPAuthorizationCredentials | None = Depends(agent_bearer),
    db: Session = Depends(get_db),
) -> Agent:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing agent token")
    token_hash = hash_agent_token(creds.credentials)
    agent = db.query(Agent).filter(Agent.agent_token_hash == token_hash).first()
    if not agent or agent.status == "revoked":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or revoked agent")
    if agent.status == "pending" and not settings.auto_approve_agents:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Agent pending approval")
    return agent


def hash_agent_token(token: str) -> str:
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()
