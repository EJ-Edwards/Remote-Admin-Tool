"""
DEV ONLY — minimal local API stub for agent development.
Binds 127.0.0.1 only. Not for production.
No remote control endpoints.
"""

from __future__ import annotations

import secrets
import uuid

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Sentinel Link Dev API", docs_url="/docs")

_tokens: dict[str, dict] = {}


class EnrollRequest(BaseModel):
    enrollment_token: str
    system_name: str


class EventsBatch(BaseModel):
    events: list[dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/agents/enroll")
def enroll(body: EnrollRequest):
    agent_token = secrets.token_urlsafe(32)
    agent_id = f"agent_{uuid.uuid4().hex[:12]}"
    workspace_id = f"ws_{uuid.uuid4().hex[:8]}"
    system_id = f"sys_{uuid.uuid4().hex[:8]}"
    _tokens[agent_token] = {
        "agent_id": agent_id,
        "workspace_id": workspace_id,
        "system_id": system_id,
    }
    return {
        "agent_id": agent_id,
        "workspace_id": workspace_id,
        "system_id": system_id,
        "agent_token": agent_token,
    }


def _auth_agent(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing agent token")
    token = authorization[7:]
    if token not in _tokens:
        raise HTTPException(401, "Invalid agent token")
    return _tokens[token]


@app.post("/agent/heartbeat")
def heartbeat(authorization: str | None = Header(None)):
    _auth_agent(authorization)
    return {"status": "ok"}


@app.post("/agent/events")
def events(body: EventsBatch, authorization: str | None = Header(None)):
    _auth_agent(authorization)
    ids = [e.get("event_id", "") for e in body.events if e.get("event_id")]
    return {"accepted_event_ids": ids, "count": len(ids)}


def run_dev_server(host: str = "127.0.0.1", port: int = 8787) -> None:
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_dev_server()
