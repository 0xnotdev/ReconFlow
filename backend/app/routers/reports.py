from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.services.pdf_service import generate_report_pdf

router = APIRouter(prefix='/reports', tags=['reports'])

@router.get('/download')
def download_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    pdf_bytes = generate_report_pdf(org, db)
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=reconflow-report.pdf'}
    )
