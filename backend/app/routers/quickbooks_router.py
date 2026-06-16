from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.services import quickbooks_service

router = APIRouter(prefix='/quickbooks', tags=['quickbooks'])

@router.post('/upload-csv')
async def upload_qb_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, 'Only CSV files accepted')
    content = await file.read()
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    count = quickbooks_service.parse_qb_csv(content, str(org.id), db)
    return {'imported': count}
