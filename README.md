# Sentinel Link

Internal audit and access monitoring for SaaS teams, agencies, MSPs, and dev shops.

**Know who accessed what, who downloaded sensitive files, and what activity needs review.**

Sentinel Link is **not** a remote admin tool. It collects **safe audit metadata only** via an outbound HTTPS agent and a cloud dashboard.

## Repository structure

| Path | Description |
|------|-------------|
| [`internal agent/`](internal%20agent/) | Python CLI agent (Typer + Rich) |
| [`cloud-dashboard/`](cloud-dashboard/) | FastAPI backend + React dashboard |
| [`SENTINEL_LINK_REFACTOR_PLAN.md`](SENTINEL_LINK_REFACTOR_PLAN.md) | Architecture and migration notes |

## Quick start

### 1. Cloud dashboard

```bash
cd cloud-dashboard
docker compose up --build
```

- API: http://localhost:8000  
- UI: http://localhost:5173  

Sign up, then generate an **enrollment token** under **Agents**.

### 2. Internal agent

```bash
cd "internal agent"
pip install -e .
sentinel-link setup
sentinel-link start
```

Events from your application can be submitted via `collectors.access_events.ingest_metadata_event()`.

## Legal notice

Deploy only on systems you are authorized to monitor. Unauthorized access is prohibited. You are responsible for compliance with applicable laws.

## License

See [LICENSE](LICENSE).
