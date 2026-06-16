from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.services.reconciliation_engine import ReconciliationEngine

router = APIRouter(prefix='/reconciliation', tags=['reconciliation'])

class RunReconRequest(BaseModel):
    client_id: str

@router.post('/run')
async def run_reconciliation(
    req: RunReconRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    engine = ReconciliationEngine(str(org.id), req.client_id, db)
    result = engine.run()
    return result
