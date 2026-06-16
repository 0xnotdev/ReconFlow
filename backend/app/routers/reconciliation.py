from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.services.reconciliation_engine import ReconciliationEngine

router = APIRouter(prefix='/reconciliation', tags=['reconciliation'])

@router.post('/run')
async def run_reconciliation(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    # Run synchronously for MVP (fast enough for <10k transactions)
    engine = ReconciliationEngine(str(org.id), db)
    result = engine.run()
    return result
