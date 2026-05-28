"""Report generation — CSV export."""

import csv
import io
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import AuditEvent, Report

STORAGE = Path(__file__).resolve().parents[2] / "storage" / "reports"


def generate_csv_report(
    db: Session,
    workspace_id: str,
    title: str,
    created_by: str | None,
    start: datetime | None,
    end: datetime | None,
) -> Report:
    STORAGE.mkdir(parents=True, exist_ok=True)
    q = db.query(AuditEvent).filter(AuditEvent.workspace_id == workspace_id)
    if start:
        q = q.filter(AuditEvent.occurred_at >= start)
    if end:
        q = q.filter(AuditEvent.occurred_at <= end)
    events = q.order_by(AuditEvent.occurred_at.desc()).limit(10000).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "event_id", "event_type", "user_email", "resource_name",
        "resource_category", "result", "ip_address", "risk_level", "occurred_at",
    ])
    for e in events:
        writer.writerow([
            e.event_id, e.event_type, e.user_email or "", e.resource_name or "",
            e.resource_category or "", e.result, e.ip_address or "", e.risk_level,
            e.occurred_at.isoformat(),
        ])

    report = Report(
        workspace_id=workspace_id,
        title=title,
        report_type="csv",
        date_range_start=start,
        date_range_end=end,
        created_by=created_by,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    path = STORAGE / f"{report.id}.csv"
    path.write_text(buf.getvalue(), encoding="utf-8")
    report.download_url = f"/reports/{report.id}/download"
    db.commit()
    db.refresh(report)
    return report


def export_audit_events_csv(db: Session, workspace_id: str) -> str:
    q = db.query(AuditEvent).filter(AuditEvent.workspace_id == workspace_id)
    events = q.order_by(AuditEvent.occurred_at.desc()).limit(10000).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "event_id", "event_type", "user_email", "resource_name",
        "resource_category", "result", "ip_address", "risk_level", "occurred_at",
    ])
    for e in events:
        writer.writerow([
            e.event_id, e.event_type, e.user_email or "", e.resource_name or "",
            e.resource_category or "", e.result, e.ip_address or "", e.risk_level,
            e.occurred_at.isoformat(),
        ])
    return buf.getvalue()
