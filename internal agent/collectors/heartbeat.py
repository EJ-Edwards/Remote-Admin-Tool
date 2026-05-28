"""System heartbeat collector — safe metadata only."""

import os
import platform

from config import load_config
from models import AuditEvent, EventType, RiskLevel


def build_heartbeat_event() -> AuditEvent:
    cfg = load_config()
    return AuditEvent(
        event_type=EventType.SYSTEM_HEARTBEAT,
        workspace_id=cfg.workspace_id,
        system_id=cfg.system_id,
        agent_id=cfg.agent_id,
        device_name=os.environ.get("SENTINEL_DEVICE_NAME", platform.node()),
        risk_level=RiskLevel.LOW,
        result="success",
        metadata={
            "agent_version": "0.1.0",
            "platform": platform.system(),
            "platform_release": platform.release(),
            "hostname": platform.node(),
        },
    )
