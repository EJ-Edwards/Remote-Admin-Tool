# Sentinel Link — Internal Agent

Outbound-only CLI agent for access monitoring and audit metadata sync.

**Not a remote admin tool.** The agent does not execute commands from the cloud, open inbound control ports, or collect passwords, file contents, keystrokes, or screenshots.

## Install

```bash
cd "internal agent"
pip install -e .
```

## Commands

| Command | Description |
|---------|-------------|
| `sentinel-link setup` | Guided setup (API URL, enrollment token, system name) |
| `sentinel-link enroll --token <token>` | Enroll with cloud dashboard |
| `sentinel-link start` | Run heartbeat + event sync loop |
| `sentinel-link status` | Agent status (secrets redacted) |
| `sentinel-link sync` | Manually flush offline queue |
| `sentinel-link test-event` | Send one `system.heartbeat` to verify connectivity |
| `sentinel-link config` | Show config (tokens redacted) |

## Local dev API (optional)

```bash
python server.py
```

Runs a **DEV ONLY** stub on `127.0.0.1:8787`. Set `api_base_url` to `http://127.0.0.1:8787` in setup for offline API testing.

## Config

Stored at `~/.sentinel-link/config.json` (tokens never printed by CLI).

## Application hooks

Use `collectors.access_events.ingest_metadata_event()` from your app to queue safe audit metadata. See that module for integration notes.
