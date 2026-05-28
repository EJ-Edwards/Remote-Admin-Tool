"""
Sentinel Link CLI — internal audit agent (outbound HTTPS only).
"""

from __future__ import annotations

import logging
import time

import typer
from rich.console import Console
from rich.table import Table

from client import CloudClient, CloudClientError
from collectors.heartbeat import build_heartbeat_event
from config import load_config, update_config, AgentConfig, DEFAULT_API_URL
from event_queue import enqueue_event, fetch_pending, mark_synced, pending_count
from utils.logging import setup_logging

app = typer.Typer(
    name="sentinel-link",
    help="Sentinel Link internal agent — access monitoring metadata only.",
    no_args_is_help=True,
)
console = Console()
logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_SEC = 60


def _require_enrolled() -> AgentConfig:
    cfg = load_config()
    if not cfg.is_enrolled():
        console.print("[red]Agent not enrolled. Run: sentinel-link enroll --token <token>[/red]")
        raise typer.Exit(1)
    return cfg


def _sync_queue(client: CloudClient) -> int:
    pending = fetch_pending()
    if not pending:
        return 0
    try:
        accepted = client.send_events(pending)
        mark_synced(accepted)
        return len(accepted)
    except CloudClientError as e:
        logger.error("Sync failed: %s", e)
        return 0


@app.command()
def setup(
    api_url: str = typer.Option(DEFAULT_API_URL, prompt="Cloud API URL"),
) -> None:
    """Guided setup: API URL, enrollment token, system name."""
    token = typer.prompt("Enrollment token")
    system_name = typer.prompt("System name", default="production-app")
    update_config(api_base_url=api_url.rstrip("/"), system_name=system_name)
    client = CloudClient()
    if not client.health_check():
        console.print("[yellow]Warning: cloud API health check failed.[/yellow]")
    else:
        console.print("[green]Cloud API reachable.[/green]")
    try:
        client.enroll(token, system_name)
        console.print("[green]Enrolled successfully.[/green]")
    except CloudClientError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def enroll(
    token: str = typer.Option(..., "--token", help="Workspace enrollment token"),
    system_name: str | None = typer.Option(None, help="Override system name from config"),
) -> None:
    """Enroll this agent with the cloud dashboard."""
    cfg = load_config()
    name = system_name or cfg.system_name
    client = CloudClient()
    try:
        client.enroll(token, name)
        console.print("[green]Enrolled successfully.[/green]")
        status()
    except CloudClientError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def start(
    interval: int = typer.Option(HEARTBEAT_INTERVAL_SEC, help="Heartbeat interval (seconds)"),
) -> None:
    """Run agent loop: heartbeat + sync queued events."""
    setup_logging()
    _require_enrolled()
    client = CloudClient()
    console.print("[green]Sentinel Link agent running. Ctrl+C to stop.[/green]")
    try:
        while True:
            hb = build_heartbeat_event()
            enqueue_event(hb.to_api_dict())
            try:
                client.send_heartbeat()
                synced = _sync_queue(client)
                if synced:
                    logger.info("Synced %s event(s)", synced)
            except CloudClientError as e:
                logger.warning("Cloud unreachable, events queued locally: %s", e)
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]Agent stopped.[/yellow]")


@app.command()
def status() -> None:
    """Show agent status (secrets redacted)."""
    cfg = load_config()
    client = CloudClient(cfg)
    online = client.health_check() if cfg.api_base_url else False
    table = Table(title="Sentinel Link Agent")
    for key, val in cfg.safe_dict().items():
        table.add_row(key, str(val))
    table.add_row("queue_length", str(pending_count()))
    table.add_row("connection_status", "online" if online else "offline")
    console.print(table)


@app.command()
def sync() -> None:
    """Manually sync queued events to the cloud."""
    _require_enrolled()
    client = CloudClient()
    n = _sync_queue(client)
    console.print(f"[green]Synced {n} event(s).[/green]")


@app.command("test-event")
def test_event() -> None:
    """Send a single system.heartbeat to verify cloud connectivity."""
    _require_enrolled()
    client = CloudClient()
    event = build_heartbeat_event()
    try:
        accepted = client.send_events([event.to_api_dict()])
        console.print(f"[green]Heartbeat sent. Accepted: {accepted}[/green]")
    except CloudClientError as e:
        enqueue_event(event.to_api_dict())
        console.print(f"[yellow]Queued locally: {e}[/yellow]")


@app.command()
def config() -> None:
    """Show configuration (tokens redacted)."""
    cfg = load_config()
    for key, val in cfg.safe_dict().items():
        console.print(f"{key}: {val}")


if __name__ == "__main__":
    app()
