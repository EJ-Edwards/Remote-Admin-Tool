from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Report, User
from app.schemas import ReportCreate, ReportOut
from app.services.reports import STORAGE, generate_csv_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportOut])
def list_reports(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Report)
        .filter(Report.workspace_id == user.workspace_id)
        .order_by(Report.created_at.desc())
        .all()
    )


@router.post("", response_model=ReportOut)
def create_report(
    body: ReportCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return generate_csv_report(
        db,
        user.workspace_id,
        body.title,
        user.id,
        body.date_range_start,
        body.date_range_end,
    )


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.id == report_id, Report.workspace_id == user.workspace_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    return report


@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.id == report_id, Report.workspace_id == user.workspace_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    path = STORAGE / f"{report_id}.csv"
    if not path.exists():
        raise HTTPException(404, "Report file not found")
    return FileResponse(path, filename=f"{report.title}.csv", media_type="text/csv")


@router.get("/{report_id}/pdf")
def download_pdf_placeholder(report_id: str):
    raise HTTPException(501, "PDF export coming soon")
