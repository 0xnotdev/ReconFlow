from fastapi import APIRouter, Depends, Query, HTTPException
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
    client_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    issue_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    q = db.query(Discrepancy).filter(Discrepancy.org_id == org.id)
    if client_id: q = q.filter(Discrepancy.client_id == client_id)
    if status: q = q.filter(Discrepancy.status == status)
    if issue_type: q = q.filter(Discrepancy.issue_type == issue_type)
    total = q.count()
    items = q.order_by(Discrepancy.detected_at.desc()).offset(offset).limit(limit).all()
    return {'total': total, 'items': [_serialize(d) for d in items]}

@router.get('/summary')
async def get_summary(
    client_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    from app.models.stripe_transaction import StripeTransaction
    
    disc_q = db.query(Discrepancy).filter(Discrepancy.org_id == org.id, Discrepancy.status == 'open')
    stripe_q = db.query(StripeTransaction).filter(StripeTransaction.org_id == org.id, StripeTransaction.status == 'succeeded')
    
    if client_id:
        disc_q = disc_q.filter(Discrepancy.client_id == client_id)
        stripe_q = stripe_q.filter(StripeTransaction.client_id == client_id)
        
    open_discs = disc_q.all()
    total_reconciled = stripe_q.count()
    return {
        'money_reconciled': sum(t.amount for t in stripe_q.all()),
        'money_at_risk': sum(d.amount or 0 for d in open_discs),
        'recoverable_amount': sum(d.recoverable_amount or 0 for d in open_discs),
        'issues_found': len(open_discs),
    }

@router.get('/audit')
async def get_real_audit(
    client_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from datetime import datetime
    from app.models.discrepancy import DiscrepancyStatus

    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    if not org:
        raise HTTPException(status_code=404, detail='Organization not found')

    open_discs = db.query(Discrepancy).filter(
        Discrepancy.org_id == org.id,
        Discrepancy.status == DiscrepancyStatus.OPEN
    ).order_by(Discrepancy.amount.desc()).all()

    # Compute metrics
    revenue_at_risk = sum(d.amount or 0 for d in open_discs)
    recoverable = sum(d.recoverable_amount or 0 for d in open_discs)
    critical = sum(1 for d in open_discs if (d.confidence_score or 0) >= 0.90)

    # Build findings data
    findings = []
    for d in open_discs:
        severity = 'critical' if (d.confidence_score or 0) >= 0.90 else 'warning' if (d.confidence_score or 0) >= 0.80 else 'info'
        findings.append({
            'id': str(d.id),
            'issue_type': d.issue_type.value,
            'severity': severity,
            'amount': d.amount or 0,
            'financial_impact': d.amount or 0,
            'recoverable_amount': d.recoverable_amount or 0,
            'customer_name': d.customer_name,
            'date': d.date.strftime('%Y-%m-%d') if d.date else None,
            'what_happened': d.suggested_cause or f'A discrepancy of ${d.amount or 0:,.2f} was detected.',
            'why_it_matters': d.why_it_matters or 'This discrepancy impacts your books and financial reporting.',
            'recommended_action': d.recommended_action or 'Investigate and match the transactions.',
            'root_cause': d.suggested_cause or 'Mismatch between data sources',
            'confidence_score': d.confidence_score or 0,
        })

    # Impact breakdown
    breakdown_map = {}
    for f in findings:
        it = f['issue_type']
        if it not in breakdown_map:
            breakdown_map[it] = {'issue_type': it, 'count': 0, 'total_impact': 0, 'total_recoverable': 0}
        breakdown_map[it]['count'] += 1
        breakdown_map[it]['total_impact'] = round(breakdown_map[it]['total_impact'] + f['financial_impact'], 2)
        breakdown_map[it]['total_recoverable'] = round(breakdown_map[it]['total_recoverable'] + f['recoverable_amount'], 2)
    
    # Root causes
    causes_map = {}
    for d in open_discs:
        rc = d.suggested_cause or 'Mismatch between data sources'
        if rc not in causes_map:
            causes_map[rc] = {'cause': rc, 'count': 0, 'total_impact': 0}
        causes_map[rc]['count'] += 1
        causes_map[rc]['total_impact'] = round(causes_map[rc]['total_impact'] + (d.amount or 0), 2)

    return {
        'client': {
            'id': 'real-org',
            'name': org.name,
            'revenue_at_risk': revenue_at_risk,
            'recoverable_revenue': recoverable,
            'open_findings': len(open_discs),
            'critical_findings': critical,
            'last_audit': datetime.utcnow().strftime('%Y-%m-%d'),
        },
        'company': {
            'name': org.name,
            'audit_period': 'Active Ledger Audit',
        },
        'summary': {
            'revenue_at_risk': revenue_at_risk,
            'recoverable_revenue': recoverable,
            'total_findings': len(open_discs),
            'critical_findings': critical,
        },
        'findings': findings,
        'impact_breakdown': list(breakdown_map.values()),
        'root_causes': sorted(list(causes_map.values()), key=lambda x: x['total_impact'], reverse=True),
        'trend': {
            'direction': 'stable',
            'previous_risk': revenue_at_risk,
            'current_risk': revenue_at_risk,
            'change_pct': 0.0,
        }
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
