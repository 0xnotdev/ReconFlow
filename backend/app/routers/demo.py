"""
Demo endpoint — no authentication required.
Returns realistic sample audit data for a fictional company.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from datetime import datetime, timedelta
import random

router = APIRouter(prefix='/demo', tags=['demo'])

SAMPLE_COMPANY = {
    'id': 'demo-acme-001',
    'name': 'Acme Commerce Co.',
    'industry': 'E-commerce / SaaS',
    'audit_period': 'January 1 – March 31, 2024',
    'generated_at': None,  # filled at request time
}

SAMPLE_CLIENTS = [
    {
        'id': 'client-001',
        'name': 'Acme Commerce Co.',
        'revenue_at_risk': 14820.00,
        'recoverable_revenue': 11640.00,
        'open_findings': 12,
        'critical_findings': 5,
        'last_audit': '2024-03-28',
    },
    {
        'id': 'client-002',
        'name': 'Bloom & Vine Studio',
        'revenue_at_risk': 8340.00,
        'recoverable_revenue': 6120.00,
        'open_findings': 8,
        'critical_findings': 3,
        'last_audit': '2024-03-25',
    },
    {
        'id': 'client-003',
        'name': 'NovaTech Solutions',
        'revenue_at_risk': 22150.00,
        'recoverable_revenue': 18400.00,
        'open_findings': 15,
        'critical_findings': 7,
        'last_audit': '2024-03-30',
    },
    {
        'id': 'client-004',
        'name': 'Meridian Health Supply',
        'revenue_at_risk': 5670.00,
        'recoverable_revenue': 4200.00,
        'open_findings': 6,
        'critical_findings': 2,
        'last_audit': '2024-03-22',
    },
    {
        'id': 'client-005',
        'name': 'Peak Performance Gear',
        'revenue_at_risk': 31200.00,
        'recoverable_revenue': 24800.00,
        'open_findings': 18,
        'critical_findings': 9,
        'last_audit': '2024-03-29',
    },
]

SAMPLE_FINDINGS = [
    {
        'id': 'finding-001',
        'issue_type': 'missing_transaction',
        'severity': 'critical',
        'status': 'open',
        'amount': 2400.00,
        'financial_impact': 2400.00,
        'recoverable_amount': 2400.00,
        'customer_name': 'Sarah Mitchell',
        'customer_email': 'sarah@mitchelldesigns.com',
        'date': '2024-02-14',
        'stripe_ref': 'ch_3PqR5s7tUvWxYz',
        'shopify_ref': None,
        'qb_ref': None,
        'confidence_score': 0.94,
        'what_happened': 'A Stripe payment of $2,400.00 was received on February 14 but has no corresponding entry in QuickBooks.',
        'why_it_matters': 'This revenue is not reflected in your books. Your financial statements understate income by $2,400.00, which affects tax filings and profitability reporting.',
        'recommended_action': 'Locate the Stripe charge ch_3PqR5s7tUvWxYz in your Stripe dashboard. Create a matching Sales Receipt or Payment entry in QuickBooks for $2,400.00 dated February 14, 2024.',
        'root_cause': 'Payment received outside normal invoicing workflow',
    },
    {
        'id': 'finding-002',
        'issue_type': 'duplicate_transaction',
        'severity': 'critical',
        'status': 'open',
        'amount': 1850.00,
        'financial_impact': 1850.00,
        'recoverable_amount': 1850.00,
        'customer_name': 'James Whitfield',
        'customer_email': 'james@whitfieldcorp.com',
        'date': '2024-01-22',
        'stripe_ref': None,
        'shopify_ref': None,
        'qb_ref': 'QB-8847',
        'confidence_score': 0.92,
        'what_happened': 'A QuickBooks payment entry for $1,850.00 from James Whitfield appears twice on January 22.',
        'why_it_matters': 'Revenue is overstated by $1,850.00. This creates a false picture of income and may result in overpaying taxes.',
        'recommended_action': 'Open QuickBooks and search for payments from James Whitfield on January 22. Delete the duplicate entry (QB-8847) and verify the remaining entry matches the Stripe charge.',
        'root_cause': 'Manual data entry resulted in duplicate record',
    },
    {
        'id': 'finding-003',
        'issue_type': 'refund_mismatch',
        'severity': 'critical',
        'status': 'open',
        'amount': 3200.00,
        'financial_impact': 3200.00,
        'recoverable_amount': 0.00,
        'customer_name': 'Elena Rodriguez',
        'customer_email': 'elena@freshlooks.co',
        'date': '2024-03-05',
        'stripe_ref': 'ch_7AbCdEfGhIjKl',
        'shopify_ref': 'SH-44291',
        'qb_ref': None,
        'confidence_score': 0.96,
        'what_happened': 'A $3,200.00 refund was processed in Stripe on March 5, but no credit memo or refund entry exists in QuickBooks.',
        'why_it_matters': 'Your books still show this as earned revenue. This overstates income by $3,200.00 and could trigger audit findings.',
        'recommended_action': 'Create a Credit Memo in QuickBooks for $3,200.00 to Elena Rodriguez dated March 5, 2024. Link it to the original invoice if applicable.',
        'root_cause': 'Refund processed in payment gateway but not recorded in accounting system',
    },
    {
        'id': 'finding-004',
        'issue_type': 'revenue_leak',
        'severity': 'critical',
        'status': 'open',
        'amount': 1200.00,
        'financial_impact': 1200.00,
        'recoverable_amount': 1200.00,
        'customer_name': 'David Park',
        'customer_email': 'david@parkenterprises.io',
        'date': '2024-02-28',
        'stripe_ref': None,
        'shopify_ref': 'SH-44587',
        'qb_ref': None,
        'confidence_score': 0.88,
        'what_happened': 'Shopify order SH-44587 for $1,200.00 is marked as paid via Stripe, but no matching Stripe charge was found.',
        'why_it_matters': 'This could mean payment was never actually collected, resulting in $1,200.00 of lost revenue.',
        'recommended_action': 'Check Shopify order SH-44587 payment details. Verify whether payment was collected through an alternative gateway. If unpaid, contact the customer to collect the outstanding amount.',
        'root_cause': 'Payment gateway mismatch between Shopify and Stripe',
    },
    {
        'id': 'finding-005',
        'issue_type': 'chargeback_mismatch',
        'severity': 'critical',
        'status': 'open',
        'amount': 890.00,
        'financial_impact': 890.00,
        'recoverable_amount': 0.00,
        'customer_name': 'Monica Chen',
        'customer_email': 'monica@chen.design',
        'date': '2024-03-12',
        'stripe_ref': 'ch_9MnOpQrStUvWx',
        'shopify_ref': None,
        'qb_ref': None,
        'confidence_score': 0.91,
        'what_happened': 'A chargeback dispute for $890.00 was filed in Stripe on March 12, but no corresponding adjustment exists in QuickBooks.',
        'why_it_matters': 'Revenue is overstated by $890.00. The lost funds from the chargeback are not reflected in your financial statements.',
        'recommended_action': 'Create a Journal Entry in QuickBooks to record the chargeback loss of $890.00. Debit the chargeback expense account and credit Accounts Receivable.',
        'root_cause': 'Chargeback processed by payment gateway without accounting notification',
    },
    {
        'id': 'finding-006',
        'issue_type': 'fee_variance',
        'severity': 'warning',
        'status': 'open',
        'amount': 145.60,
        'financial_impact': 145.60,
        'recoverable_amount': 145.60,
        'customer_name': 'Multiple Transactions',
        'customer_email': None,
        'date': '2024-01-01',
        'stripe_ref': 'multiple',
        'shopify_ref': None,
        'qb_ref': None,
        'confidence_score': 0.78,
        'what_happened': 'Processing fees across 23 transactions in January exceeded the expected Stripe rate by a total of $145.60.',
        'why_it_matters': 'You may be on a non-standard pricing plan or experiencing unexpected fee increases that reduce net revenue.',
        'recommended_action': 'Review your Stripe pricing plan at dashboard.stripe.com/settings/billing. Compare actual fees against your negotiated rate. Contact Stripe support if fees exceed your agreed terms.',
        'root_cause': 'Processing fee rate differs from standard published rate',
    },
    {
        'id': 'finding-007',
        'issue_type': 'missing_transaction',
        'severity': 'warning',
        'status': 'open',
        'amount': 780.00,
        'financial_impact': 780.00,
        'recoverable_amount': 780.00,
        'customer_name': 'Taylor Brooks',
        'customer_email': 'taylor@brooksagency.com',
        'date': '2024-03-18',
        'stripe_ref': 'ch_2YzAbCdEfGhIj',
        'shopify_ref': None,
        'qb_ref': None,
        'confidence_score': 0.87,
        'what_happened': 'A Stripe payment of $780.00 from Taylor Brooks on March 18 has no corresponding QuickBooks entry.',
        'why_it_matters': 'Revenue is understated. This payment is not reflected in your accounting records.',
        'recommended_action': 'Create a Sales Receipt in QuickBooks for $780.00 from Taylor Brooks dated March 18, 2024. Reference Stripe charge ch_2YzAbCdEfGhIj.',
        'root_cause': 'Payment received outside normal invoicing workflow',
    },
    {
        'id': 'finding-008',
        'issue_type': 'revenue_leak',
        'severity': 'warning',
        'status': 'open',
        'amount': 2150.00,
        'financial_impact': 2150.00,
        'recoverable_amount': 2150.00,
        'customer_name': 'Priya Sharma',
        'customer_email': 'priya@sharmaco.in',
        'date': '2024-02-10',
        'stripe_ref': None,
        'shopify_ref': 'SH-44102',
        'qb_ref': None,
        'confidence_score': 0.82,
        'what_happened': 'Shopify order SH-44102 for $2,150.00 shows as paid but has no matching payment in Stripe.',
        'why_it_matters': 'If payment was never collected, this represents $2,150.00 of unrecovered revenue.',
        'recommended_action': 'Verify payment status for Shopify order SH-44102. If payment was received through another gateway, reconcile accordingly. If unpaid, initiate collection.',
        'root_cause': 'Payment gateway mismatch between Shopify and Stripe',
    },
    {
        'id': 'finding-009',
        'issue_type': 'missing_transaction',
        'severity': 'info',
        'status': 'open',
        'amount': 450.00,
        'financial_impact': 450.00,
        'recoverable_amount': 450.00,
        'customer_name': 'Alex Johnson',
        'customer_email': 'alex@alexjohnson.dev',
        'date': '2024-01-30',
        'stripe_ref': 'ch_4KlMnOpQrStUv',
        'shopify_ref': None,
        'qb_ref': None,
        'confidence_score': 0.83,
        'what_happened': 'A $450.00 Stripe charge from Alex Johnson on January 30 is missing from QuickBooks.',
        'why_it_matters': 'Revenue is understated by $450.00 in your January records.',
        'recommended_action': 'Add a Payment entry in QuickBooks for $450.00 from Alex Johnson, dated January 30, 2024.',
        'root_cause': 'Payment received outside normal invoicing workflow',
    },
    {
        'id': 'finding-010',
        'issue_type': 'refund_mismatch',
        'severity': 'warning',
        'status': 'open',
        'amount': 560.00,
        'financial_impact': 560.00,
        'recoverable_amount': 0.00,
        'customer_name': 'Rachel Kim',
        'customer_email': 'rachel@kimstudio.com',
        'date': '2024-02-20',
        'stripe_ref': 'ch_5WxYzAbCdEfGh',
        'shopify_ref': None,
        'qb_ref': None,
        'confidence_score': 0.90,
        'what_happened': 'A $560.00 partial refund was issued in Stripe on February 20 but is not recorded in QuickBooks.',
        'why_it_matters': 'Revenue is overstated by $560.00. Financial statements do not accurately reflect the refund.',
        'recommended_action': 'Create a Credit Memo in QuickBooks for $560.00 to Rachel Kim dated February 20, 2024.',
        'root_cause': 'Refund processed in payment gateway but not recorded in accounting system',
    },
    {
        'id': 'finding-011',
        'issue_type': 'fee_variance',
        'severity': 'info',
        'status': 'open',
        'amount': 89.40,
        'financial_impact': 89.40,
        'recoverable_amount': 89.40,
        'customer_name': 'Multiple Transactions',
        'customer_email': None,
        'date': '2024-02-01',
        'stripe_ref': 'multiple',
        'shopify_ref': None,
        'qb_ref': None,
        'confidence_score': 0.74,
        'what_happened': 'February processing fees exceeded expected rates by $89.40 across 18 transactions.',
        'why_it_matters': 'Accumulated fee overcharges reduce net revenue over time.',
        'recommended_action': 'Audit February Stripe fee statements. Compare line-item fees against your published or negotiated rate.',
        'root_cause': 'Processing fee rate differs from standard published rate',
    },
    {
        'id': 'finding-012',
        'issue_type': 'duplicate_transaction',
        'severity': 'info',
        'status': 'open',
        'amount': 1105.00,
        'financial_impact': 1105.00,
        'recoverable_amount': 1105.00,
        'customer_name': 'Marcus Webb',
        'customer_email': 'marcus@webbconsulting.com',
        'date': '2024-03-01',
        'stripe_ref': None,
        'shopify_ref': None,
        'qb_ref': 'QB-9213',
        'confidence_score': 0.88,
        'what_happened': 'A $1,105.00 payment from Marcus Webb on March 1 appears twice in QuickBooks.',
        'why_it_matters': 'Revenue is overstated by $1,105.00 due to the duplicate entry.',
        'recommended_action': 'Search QuickBooks for payments from Marcus Webb on March 1, 2024. Remove the duplicate entry QB-9213.',
        'root_cause': 'Manual data entry resulted in duplicate record',
    },
]


def _compute_summary(findings):
    revenue_at_risk = sum(f['financial_impact'] for f in findings)
    recoverable = sum(f['recoverable_amount'] for f in findings)
    critical = sum(1 for f in findings if f['severity'] == 'critical')
    return {
        'revenue_at_risk': round(revenue_at_risk, 2),
        'recoverable_revenue': round(recoverable, 2),
        'total_findings': len(findings),
        'critical_findings': critical,
        'warning_findings': sum(1 for f in findings if f['severity'] == 'warning'),
        'info_findings': sum(1 for f in findings if f['severity'] == 'info'),
    }


def _compute_impact_breakdown(findings):
    breakdown = {}
    for f in findings:
        it = f['issue_type']
        if it not in breakdown:
            breakdown[it] = {'issue_type': it, 'count': 0, 'total_impact': 0, 'total_recoverable': 0}
        breakdown[it]['count'] += 1
        breakdown[it]['total_impact'] = round(breakdown[it]['total_impact'] + f['financial_impact'], 2)
        breakdown[it]['total_recoverable'] = round(breakdown[it]['total_recoverable'] + f['recoverable_amount'], 2)
    return list(breakdown.values())


def _compute_root_causes(findings):
    causes = {}
    for f in findings:
        rc = f['root_cause']
        if rc not in causes:
            causes[rc] = {'cause': rc, 'count': 0, 'total_impact': 0}
        causes[rc]['count'] += 1
        causes[rc]['total_impact'] = round(causes[rc]['total_impact'] + f['financial_impact'], 2)
    return sorted(causes.values(), key=lambda x: x['total_impact'], reverse=True)


def _compute_actions(findings):
    actions = []
    seen = set()
    for f in sorted(findings, key=lambda x: x['financial_impact'], reverse=True):
        action_key = f['recommended_action'][:60]
        if action_key not in seen:
            seen.add(action_key)
            actions.append({
                'priority': 'high' if f['severity'] == 'critical' else 'medium' if f['severity'] == 'warning' else 'low',
                'action': f['recommended_action'],
                'impact': f['financial_impact'],
                'finding_id': f['id'],
            })
    return actions


@router.get('/audit')
def get_demo_audit():
    """Full demo audit — no auth required."""
    company = {**SAMPLE_COMPANY, 'generated_at': datetime.utcnow().isoformat()}
    summary = _compute_summary(SAMPLE_FINDINGS)
    impact_breakdown = _compute_impact_breakdown(SAMPLE_FINDINGS)
    root_causes = _compute_root_causes(SAMPLE_FINDINGS)
    actions = _compute_actions(SAMPLE_FINDINGS)

    return {
        'company': company,
        'summary': summary,
        'findings': SAMPLE_FINDINGS,
        'impact_breakdown': impact_breakdown,
        'root_causes': root_causes,
        'recommended_actions': actions,
        'trend': {
            'direction': 'improving',
            'previous_risk': 18420.00,
            'current_risk': summary['revenue_at_risk'],
            'change_pct': round(
                ((summary['revenue_at_risk'] - 18420.00) / 18420.00) * 100, 1
            ),
        },
    }


@router.get('/clients')
def get_demo_clients():
    """Demo client list for agency workspace."""
    return {
        'agency_name': 'Sterling & Associates',
        'clients': sorted(SAMPLE_CLIENTS, key=lambda c: c['revenue_at_risk'], reverse=True),
        'totals': {
            'total_revenue_at_risk': sum(c['revenue_at_risk'] for c in SAMPLE_CLIENTS),
            'total_recoverable': sum(c['recoverable_revenue'] for c in SAMPLE_CLIENTS),
            'total_findings': sum(c['open_findings'] for c in SAMPLE_CLIENTS),
            'total_critical': sum(c['critical_findings'] for c in SAMPLE_CLIENTS),
        },
    }


@router.get('/client/{client_id}')
def get_demo_client_audit(client_id: str):
    """Demo client audit for a specific client."""
    client = next((c for c in SAMPLE_CLIENTS if c['id'] == client_id), SAMPLE_CLIENTS[0])
    company = {**SAMPLE_COMPANY, 'name': client['name'], 'generated_at': datetime.utcnow().isoformat()}
    summary = _compute_summary(SAMPLE_FINDINGS)
    summary['revenue_at_risk'] = client['revenue_at_risk']
    summary['recoverable_revenue'] = client['recoverable_revenue']
    summary['total_findings'] = client['open_findings']
    summary['critical_findings'] = client['critical_findings']

    return {
        'client': client,
        'company': company,
        'summary': summary,
        'findings': SAMPLE_FINDINGS[:client['open_findings']],
        'impact_breakdown': _compute_impact_breakdown(SAMPLE_FINDINGS[:client['open_findings']]),
        'root_causes': _compute_root_causes(SAMPLE_FINDINGS[:client['open_findings']]),
        'recommended_actions': _compute_actions(SAMPLE_FINDINGS[:client['open_findings']]),
        'trend': {
            'direction': 'improving',
            'previous_risk': client['revenue_at_risk'] * 1.15,
            'current_risk': client['revenue_at_risk'],
            'change_pct': -13.0,
        },
    }

@router.post('/load-sample-data')
async def load_sample_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.organization import Organization
    from app.models.stripe_transaction import StripeTransaction
    from app.models.shopify_order import ShopifyOrder
    from app.models.quickbooks_entry import QuickBooksEntry
    from app.models.discrepancy import Discrepancy, DiscrepancyStatus, IssueType
    from fastapi import HTTPException

    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    if not org:
        raise HTTPException(status_code=404, detail='Organization not found')

    # Clear existing data for this organization
    db.query(StripeTransaction).filter(StripeTransaction.org_id == org.id).delete()
    db.query(QuickBooksEntry).filter(QuickBooksEntry.org_id == org.id).delete()
    db.query(ShopifyOrder).filter(ShopifyOrder.org_id == org.id).delete()
    db.query(Discrepancy).filter(Discrepancy.org_id == org.id).delete()
    db.commit()

    import_time = datetime.utcnow()
    
    # 1. Reconciled entries helper
    reconciled_txns = [
        {"id": "rec_001", "name": "Alice Vance", "amount": 150.00, "date": import_time - timedelta(days=12)},
        {"id": "rec_002", "name": "Bob Miller", "amount": 450.00, "date": import_time - timedelta(days=10)},
        {"id": "rec_003", "name": "Charlie King", "amount": 890.00, "date": import_time - timedelta(days=8)},
        {"id": "rec_004", "name": "Diana Ross", "amount": 1250.00, "date": import_time - timedelta(days=6)},
        {"id": "rec_005", "name": "Ethan Hunt", "amount": 3200.00, "date": import_time - timedelta(days=4)},
    ]
    
    def get_fee(amt):
        return round(amt * 0.029 + 0.30, 2)

    for r in reconciled_txns:
        db.add(StripeTransaction(
            org_id=org.id, stripe_id=f"ch_{r['id']}", amount=r['amount'], status="succeeded",
            customer_name=r['name'], stripe_fee=get_fee(r['amount']), net_amount=r['amount'] - get_fee(r['amount']),
            created_at=r['date'], imported_at=import_time
        ))
        db.add(ShopifyOrder(
            org_id=org.id, shopify_id=f"sh_{r['id']}", order_number=f"100_{r['id']}", total_price=r['amount'],
            financial_status="paid", customer_name=r['name'], gateway="stripe", created_at=r['date'], imported_at=import_time
        ))
        db.add(QuickBooksEntry(
            org_id=org.id, qb_id=f"qb_{r['id']}", transaction_type="SalesReceipt", amount=r['amount'],
            customer_name=r['name'], txn_date=r['date'], imported_at=import_time
        ))

    # 2. Missing in QB
    db.add(StripeTransaction(
        org_id=org.id, stripe_id="ch_miss_001", amount=2400.00, status="succeeded",
        customer_name="Sarah Mitchell", customer_email="sarah@mitchelldesigns.com",
        stripe_fee=get_fee(2400.00), net_amount=2400.00 - get_fee(2400.00),
        created_at=import_time - timedelta(days=5), imported_at=import_time
    ))
    db.add(ShopifyOrder(
        org_id=org.id, shopify_id="sh_miss_001", order_number="10098", total_price=2400.00,
        financial_status="paid", customer_name="Sarah Mitchell", customer_email="sarah@mitchelldesigns.com",
        gateway="stripe", created_at=import_time - timedelta(days=5), imported_at=import_time
    ))

    # 3. Duplicate QB
    db.add(StripeTransaction(
        org_id=org.id, stripe_id="ch_dup_001", amount=1850.00, status="succeeded",
        customer_name="James Whitfield", customer_email="james@whitfieldcorp.com",
        stripe_fee=get_fee(1850.00), net_amount=1850.00 - get_fee(1850.00),
        created_at=import_time - timedelta(days=15), imported_at=import_time
    ))
    db.add(QuickBooksEntry(
        org_id=org.id, qb_id="qb_dup_001a", transaction_type="Payment", amount=1850.00,
        customer_name="James Whitfield", customer_email="james@whitfieldcorp.com",
        txn_date=import_time - timedelta(days=15), imported_at=import_time
    ))
    db.add(QuickBooksEntry(
        org_id=org.id, qb_id="qb_dup_001b", transaction_type="Payment", amount=1850.00,
        customer_name="James Whitfield", customer_email="james@whitfieldcorp.com",
        txn_date=import_time - timedelta(days=15), imported_at=import_time
    ))

    # 4. Refund Mismatch
    db.add(StripeTransaction(
        org_id=org.id, stripe_id="ch_ref_001", amount=3200.00, status="refunded",
        customer_name="Elena Rodriguez", customer_email="elena@freshlooks.co",
        refunded=True, refund_amount=3200.00,
        created_at=import_time - timedelta(days=20), imported_at=import_time
    ))
    db.add(QuickBooksEntry(
        org_id=org.id, qb_id="qb_ref_orig", transaction_type="SalesReceipt", amount=3200.00,
        customer_name="Elena Rodriguez", customer_email="elena@freshlooks.co",
        txn_date=import_time - timedelta(days=20), imported_at=import_time
    ))

    # 5. Revenue Leak
    db.add(ShopifyOrder(
        org_id=org.id, shopify_id="sh_leak_001", order_number="10105", total_price=1200.00,
        financial_status="paid", customer_name="David Park", customer_email="david@parkenterprises.io",
        gateway="stripe", created_at=import_time - timedelta(days=3), imported_at=import_time
    ))

    # 6. Chargeback Dispute Mismatch
    db.add(StripeTransaction(
        org_id=org.id, stripe_id="ch_dis_001", amount=890.00, status="succeeded", disputed=True,
        customer_name="Monica Chen", customer_email="monica@chen.design",
        created_at=import_time - timedelta(days=2), imported_at=import_time
    ))
    db.add(QuickBooksEntry(
        org_id=org.id, qb_id="qb_dis_orig", transaction_type="SalesReceipt", amount=890.00,
        customer_name="Monica Chen", customer_email="monica@chen.design",
        txn_date=import_time - timedelta(days=2), imported_at=import_time
    ))

    # 7. Fee Variance
    db.add(StripeTransaction(
        org_id=org.id, stripe_id="ch_fee_001", amount=5000.00, status="succeeded",
        customer_name="Peak Performance Gear", stripe_fee=250.00, net_amount=4750.00,
        created_at=import_time - timedelta(days=1), imported_at=import_time
    ))
    db.add(QuickBooksEntry(
        org_id=org.id, qb_id="qb_fee_orig", transaction_type="SalesReceipt", amount=4750.00,
        customer_name="Peak Performance Gear", txn_date=import_time - timedelta(days=1), imported_at=import_time
    ))

    db.commit()

    from app.services.reconciliation_engine import ReconciliationEngine
    engine = ReconciliationEngine(str(org.id), db)
    result = engine.run()

    return {
        "status": "success",
        "message": "Sample data loaded and reconciliation run successfully.",
        "details": result
    }
