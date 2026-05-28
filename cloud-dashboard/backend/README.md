# Sentinel Link — Cloud API

FastAPI backend for workspaces, agents, audit events, alerts, and reports.

## Run with Docker

```bash
cd cloud-dashboard
docker compose up --build
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

## Environment

| Variable | Default |
|----------|---------|
| `DATABASE_URL` | `postgresql://sentinel:sentinel@postgres:5432/sentinel_link` |
| `JWT_SECRET` | Change in production |
| `AUTO_APPROVE_AGENTS` | `true` (set `false` in production) |
| `CORS_ORIGINS` | `http://localhost:5173` |

## Local run (without Docker)

```bash
pip install -r requirements.txt
export DATABASE_URL=postgresql://sentinel:sentinel@localhost:5432/sentinel_link
uvicorn app.main:app --reload --app-dir .
```

Run from `cloud-dashboard/backend` with `PYTHONPATH=.` or use Docker.
