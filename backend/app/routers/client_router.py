from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.models.client import Client
from pydantic import BaseModel
import uuid

router = APIRouter(prefix='/clients', tags=['clients'])

class ClientCreate(BaseModel):
    name: str

@router.get('/')
def get_clients(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    clients = db.query(Client).filter(Client.org_id == org.id).all()
    
    # Calculate simple stats for each client (we can optimize this later)
    # Right now just returning the clients
    result = []
    for c in clients:
        # Sum up open discrepancies for this client
        from app.models.discrepancy import Discrepancy, DiscrepancyStatus
        open_disc = db.query(Discrepancy).filter(
            Discrepancy.client_id == c.id,
            Discrepancy.status == DiscrepancyStatus.OPEN
        ).all()
        
        rev_at_risk = sum(d.amount or 0 for d in open_disc)
        recoverable = sum(d.recoverable_amount or 0 for d in open_disc)
        critical = sum(1 for d in open_disc if (d.confidence_score or 0) >= 0.9)
        
        result.append({
            "id": str(c.id),
            "name": c.name,
            "revenue_at_risk": rev_at_risk,
            "recoverable_revenue": recoverable,
            "critical_findings": critical,
            "created_at": c.created_at
        })
        
    return result

@router.post('/')
def create_client(data: ClientCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    client = Client(
        org_id=org.id,
        name=data.name
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return {"id": str(client.id), "name": client.name}

@router.delete('/{client_id}')
def delete_client(client_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    client = db.query(Client).filter(Client.id == client_id, Client.org_id == org.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    db.delete(client)
    db.commit()
    return {"status": "success"}
