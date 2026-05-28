# Sentinel Link Refactor Plan

Living document for the audit-monitoring product refactor. See the approved plan in `.cursor/plans/` for full architecture diagrams.

## Product

**Sentinel Link** — internal CLI agent + cloud dashboard for access monitoring, audit trails, sensitive download alerts, system heartbeat, and internal activity visibility.

**Not** a remote admin tool. No remote control, shell execution, or sensitive data capture.

## Legacy files (removed)

| File | Was | Action |
|------|-----|--------|
| `internal agent/client.py` | TCP agent + remote commands + file exfil | Replaced by HTTPS `client.py` |
| `internal agent/server.py` | TCP server + Flask command UI | Replaced by dev mock API only |
| `internal agent/main.py` | Server/client menu | Replaced by Typer CLI |

## New layout

```
internal agent/          # CLI agent (outbound HTTPS only)
cloud-dashboard/
  backend/               # FastAPI + PostgreSQL
  frontend/              # Vite + React + Tailwind
  docker-compose.yml
```

## Safe audit event types

`user.login`, `user.logout`, `user.login_failed`, `resource.viewed`, `file.downloaded`, `report.exported`, `role.changed`, `member.invited`, `member.removed`, `system.heartbeat`, `system.offline`, `new_ip.detected`, `sensitive_download.detected`, `failed_access_spike.detected`, `unusual_access.detected`

## Phases

1. Internal agent CLI + queue + dev mock
2. Cloud backend (auth, workspaces, agents, audit events)
3. Agent ↔ cloud integration
4. React dashboard
5. Alert rules
6. Reports + CSV export
7. Docs and polish (no bundled demo/seed data)

## Quick start (after implementation)

```bash
# Cloud
cd cloud-dashboard && docker compose up -d

# Agent
cd "internal agent" && pip install -e .
sentinel-link setup
sentinel-link enroll --token <token>
sentinel-link start
```
