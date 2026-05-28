import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_agent, get_current_user, hash_agent_token
from app.config import settings
from app.database import get_db
from app.models import Agent, AgentEnrollmentToken, System, User
from app.schemas import (
    AgentEnrollRequest,
    AgentEnrollResponse,
    AgentOut,
    EnrollmentTokenCreate,
    EnrollmentTokenOut,
    EventsBatchIn,
    EventsBatchOut,
    HeartbeatIn,
)

router = APIRouter(tags=["agents"])


@router.post("/agents/enrollment-tokens", response_model=EnrollmentTokenOut)
def create_enrollment_token(
    body: EnrollmentTokenCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raw = secrets.token_urlsafe(32)
    row = AgentEnrollmentToken(
        workspace_id=user.workspace_id,
        token_hash=hash_agent_token(raw),
        name=body.name,
        status="active",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return EnrollmentTokenOut(id=row.id, token=raw, name=row.name, status=row.status)


@router.get("/agents", response_model=list[AgentOut])
def list_agents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Agent).filter(Agent.workspace_id == user.workspace_id).all()


@router.post("/agents/enroll", response_model=AgentEnrollResponse)
def enroll_agent(body: AgentEnrollRequest, db: Session = Depends(get_db)):
    token_hash = hash_agent_token(body.enrollment_token)
    enroll = (
        db.query(AgentEnrollmentToken)
        .filter(
            AgentEnrollmentToken.token_hash == token_hash,
            AgentEnrollmentToken.status == "active",
        )
        .first()
    )
    if not enroll:
        raise HTTPException(401, "Invalid enrollment token")
    system = System(
        workspace_id=enroll.workspace_id,
        name=body.system_name,
        type="server",
        status="active",
    )
    db.add(system)
    db.flush()
    agent_token = secrets.token_urlsafe(32)
    status = "approved" if settings.auto_approve_agents else "pending"
    agent = Agent(
        workspace_id=enroll.workspace_id,
        system_id=system.id,
        agent_name=body.system_name,
        agent_token_hash=hash_agent_token(agent_token),
        status=status,
    )
    db.add(agent)
    db.commit()
    return AgentEnrollResponse(
        agent_id=agent.id,
        workspace_id=enroll.workspace_id,
        system_id=system.id,
        agent_token=agent_token,
    )


@router.patch("/agents/{agent_id}/approve", response_model=AgentOut)
def approve_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == user.workspace_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    agent.status = "approved"
    db.commit()
    db.refresh(agent)
    return agent


@router.patch("/agents/{agent_id}/revoke", response_model=AgentOut)
def revoke_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == user.workspace_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    agent.status = "revoked"
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/agents/{agent_id}", response_model=AgentOut)
def get_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == user.workspace_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent


@router.post("/agent/heartbeat")
def agent_heartbeat(
    body: HeartbeatIn,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    agent.last_seen_at = now
    sys = db.query(System).filter(System.id == agent.system_id).first()
    if sys:
        sys.last_seen_at = now
        sys.status = "active"
    db.commit()
    return {"status": "ok"}


@router.post("/agent/events", response_model=EventsBatchOut, status_code=202)
def agent_events(
    body: EventsBatchIn,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    from app.routes.audit_events import ingest_events
    accepted = ingest_events(db, agent, body.events)
    return EventsBatchOut(accepted_event_ids=accepted, count=len(accepted))
