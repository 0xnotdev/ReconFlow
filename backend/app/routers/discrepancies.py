from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.models.discrepancy import Discrepancy, DiscrepancyStatus
from app.services.ai_explainer import generate_explanation
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter(prefix='/discrepancies', tags=['discrepancies'])

class StatusUpdate(BaseModel):
    status: str

@router.get('/')
async def list_discrepancies(
    status: Optional[str] = Query(None),
    issue_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    q = db.query(Discrepancy).filter(Discrepancy.org_id == org.id)
    if status: q = q.filter(Discrepancy.status == status)
    if issue_type: q = q.filter(Discrepancy.issue_type == issue_type)
    total = q.count()
    items = q.order_by(Discrepancy.detected_at.desc()).offset(offset).limit(limit).all()
    return {'total': total, 'items': [_serialize(d) for d in items]}

@router.get('/summary')
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    from app.models.stripe_transaction import StripeTransaction
    open_discs = db.query(Discrepancy).filter(
        Discrepancy.org_id == org.id, Discrepancy.status == 'open'
    ).all()
    total_reconciled = db.query(StripeTransaction).filter(
        StripeTransaction.org_id == org.id, StripeTransaction.status == 'succeeded'
    ).count()
    return {
        'money_reconciled': sum(
            t.amount for t in db.query(StripeTransaction).filter(
                StripeTransaction.org_id == org.id, StripeTransaction.status == 'succeeded'
            ).all()
        ),
        'money_at_risk': sum(d.amount or 0 for d in open_discs),
        'issues_found': len(open_discs),
    }

@router.patch('/{disc_id}/status')
async def update_status(
    disc_id: str,
    body: StatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    d = db.query(Discrepancy).filter(Discrepancy.id == disc_id).first()
    if not d: return {'error': 'Not found'}
    d.status = body.status
    db.commit()
    return {'ok': True}

@router.get('/{disc_id}/explain')
async def get_explanation(
    disc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    d = db.query(Discrepancy).filter(Discrepancy.id == disc_id).first()
    explanation = await generate_explanation(d)
    d.ai_explanation = explanation
    db.commit()
    return {'explanation': explanation}

def _serialize(d: Discrepancy) -> dict:
    return {
        'id': str(d.id),
        'issue_type': d.issue_type.value,
        'status': d.status.value,
        'amount': d.amount,
        'customer_name': d.customer_name,
        'date': d.date.isoformat() if d.date else None,
        'stripe_ref': d.stripe_ref,
        'shopify_ref': d.shopify_ref,
        'qb_ref': d.qb_ref,
        'confidence_score': d.confidence_score,
        'suggested_cause': d.suggested_cause,
        'ai_explanation': d.ai_explanation,
    }
