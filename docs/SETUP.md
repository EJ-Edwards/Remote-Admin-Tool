# Sentinel Link setup guide

## Prerequisites

- Docker Desktop (for cloud stack)
- Python 3.10+ (for agent)

## Cloud dashboard

1. `cd cloud-dashboard && docker compose up --build`
2. Open http://localhost:5173 and create an account.
3. Go to **Agents** → **Generate enrollment token** and copy the token.

## Internal agent

1. `cd "internal agent" && pip install -e .`
2. `sentinel-link setup` — enter API URL `http://localhost:8000`, paste enrollment token, set system name.
3. `sentinel-link start` — runs heartbeat and sync loop.
4. `sentinel-link test-event` — optional connectivity check (sends `system.heartbeat` only).

## Integrating audit events

From your application, call:

```python
from collectors.access_events import ingest_metadata_event

ingest_metadata_event({
    "event_type": "file.downloaded",
    "user_email": "user@company.com",
    "resource_name": "report.csv",
    "resource_category": "customer_data",
    "result": "success",
    "ip_address": "203.0.113.42",
})
```

Never include file contents, passwords, tokens, or keystrokes.
