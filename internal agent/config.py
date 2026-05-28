"""Local agent configuration (~/.sentinel-link/config.json)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel

CONFIG_DIR = Path.home() / ".sentinel-link"
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_API_URL = "http://localhost:8000"


class AgentConfig(BaseModel):
    agent_id: Optional[str] = None
    workspace_id: Optional[str] = None
    system_id: Optional[str] = None
    system_name: str = "default-system"
    api_base_url: str = DEFAULT_API_URL
    agent_token: Optional[str] = None
    last_sync_at: Optional[str] = None
    created_at: Optional[str] = None

    def is_enrolled(self) -> bool:
        return bool(self.agent_id and self.agent_token and self.workspace_id)

    def safe_dict(self) -> dict[str, Any]:
        d = self.model_dump()
        if d.get("agent_token"):
            d["agent_token"] = "****"
        return d


def ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> AgentConfig:
    if not CONFIG_PATH.exists():
        return AgentConfig()
    return AgentConfig(**json.loads(CONFIG_PATH.read_text(encoding="utf-8")))


def save_config(config: AgentConfig) -> None:
    ensure_config_dir()
    CONFIG_PATH.write_text(json.dumps(config.model_dump(), indent=2), encoding="utf-8")


def update_config(**kwargs: Any) -> AgentConfig:
    config = load_config()
    updated = config.model_copy(update={k: v for k, v in kwargs.items() if v is not None})
    save_config(updated)
    return updated
