from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.models.client import Client
from app.services.reconciliation_engine import ReconciliationEngine

router = APIRouter(prefix='/reconciliation', tags=['reconciliation'])

class RunReconRequest(BaseModel):
    client_id: Optional[str] = None

@router.post('/run')
async def run_reconciliation(
    req: RunReconRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    
    clients_to_run = []
    if req.client_id:
        clients_to_run = [req.client_id]
    else:
        clients_to_run = [str(c.id) for c in db.query(Client).filter(Client.org_id == org.id).all()]
        
    total_found = 0
    total_risk = 0
    for cid in clients_to_run:
        engine = ReconciliationEngine(str(org.id), cid, db)
        res = engine.run()
        total_found += res['discrepancies_found']
        total_risk += res['total_at_risk']
        
    return {
        "discrepancies_found": total_found,
        "total_at_risk": total_risk
    }
