"""SQLite offline event queue."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from config import CONFIG_DIR

QUEUE_DB = CONFIG_DIR / "events.db"


def _connect() -> sqlite3.Connection:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(QUEUE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_queue() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                synced INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()


def enqueue_event(payload: dict[str, Any]) -> None:
    init_queue()
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO pending_events (event_id, payload, synced)
            VALUES (?, ?, 0)
            """,
            (payload.get("event_id", ""), json.dumps(payload)),
        )
        conn.commit()


def pending_count() -> int:
    init_queue()
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM pending_events WHERE synced = 0"
        ).fetchone()
        return int(row["c"]) if row else 0


def fetch_pending(limit: int = 100) -> list[dict[str, Any]]:
    init_queue()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT payload FROM pending_events
            WHERE synced = 0 ORDER BY id ASC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [json.loads(r["payload"]) for r in rows]


def mark_synced(event_ids: list[str]) -> None:
    if not event_ids:
        return
    init_queue()
    placeholders = ",".join("?" * len(event_ids))
    with _connect() as conn:
        conn.execute(
            f"UPDATE pending_events SET synced = 1 WHERE event_id IN ({placeholders})",
            event_ids,
        )
        conn.commit()
