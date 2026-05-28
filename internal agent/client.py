"""
Cloud sync client — outbound HTTPS only.
Never executes commands from cloud responses.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import httpx

from config import AgentConfig, load_config, update_config
from utils.time import utc_now_iso

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


class CloudClientError(Exception):
    pass


class CloudClient:
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or load_config()

    def _base_url(self) -> str:
        return self.config.api_base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.config.agent_token:
            headers["Authorization"] = f"Bearer {self.config.agent_token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        auth: bool = True,
    ) -> httpx.Response:
        url = f"{self._base_url()}{path}"
        headers = self._headers() if auth else {"Content-Type": "application/json"}
        last_error: Optional[Exception] = None
        for attempt in range(MAX_RETRIES):
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.request(method, url, json=json, headers=headers)
                if response.status_code >= 500 and attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (attempt + 1))
                    continue
                return response
            except httpx.RequestError as e:
                last_error = e
                logger.warning("Request failed (attempt %s): %s", attempt + 1, e)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (attempt + 1))
        raise CloudClientError(f"Failed to reach {url}: {last_error}")

    def health_check(self) -> bool:
        try:
            return self._request("GET", "/health", auth=False).status_code == 200
        except CloudClientError:
            return False

    def enroll(self, enrollment_token: str, system_name: str) -> AgentConfig:
        r = self._request(
            "POST",
            "/agents/enroll",
            json={"enrollment_token": enrollment_token, "system_name": system_name},
            auth=False,
        )
        if r.status_code not in (200, 201):
            raise CloudClientError(f"Enrollment failed: {r.status_code} {r.text}")
        data = r.json()
        cfg = update_config(
            agent_id=data["agent_id"],
            workspace_id=data["workspace_id"],
            system_id=data["system_id"],
            system_name=system_name,
            agent_token=data["agent_token"],
            created_at=utc_now_iso(),
        )
        self.config = cfg
        return cfg

    def send_heartbeat(self) -> None:
        if not self.config.is_enrolled():
            raise CloudClientError("Agent not enrolled")
        r = self._request(
            "POST",
            "/agent/heartbeat",
            json={
                "agent_id": self.config.agent_id,
                "system_id": self.config.system_id,
                "device_name": self.config.system_name,
            },
        )
        if r.status_code not in (200, 201, 202, 204):
            raise CloudClientError(f"Heartbeat failed: {r.status_code} {r.text}")

    def send_events(self, events: list[dict[str, Any]]) -> list[str]:
        if not events:
            return []
        if not self.config.is_enrolled():
            raise CloudClientError("Agent not enrolled")
        r = self._request("POST", "/agent/events", json={"events": events})
        if r.status_code not in (200, 201, 202):
            raise CloudClientError(f"Event sync failed: {r.status_code} {r.text}")
        accepted = r.json().get("accepted_event_ids", [])
        update_config(last_sync_at=utc_now_iso())
        return accepted
