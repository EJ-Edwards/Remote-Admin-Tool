"""
Application-integrated audit events (metadata only).

Call ingest_metadata_event() from your app with pre-sanitized fields.
Never pass file contents, passwords, or keystrokes.
"""

from __future__ import annotations

from typing import Any

from event_queue import enqueue_event
from models import AuditEvent, EventType


def ingest_metadata_event(data: dict[str, Any]) -> AuditEvent:
    event_type = data.get("event_type")
    if isinstance(event_type, str):
        data = {**data, "event_type": EventType(event_type)}
    event = AuditEvent(**data)
    enqueue_event(event.to_api_dict())
    return event
