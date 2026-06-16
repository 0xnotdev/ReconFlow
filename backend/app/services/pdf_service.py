"""
Revenue Risk Audit — PDF Report Generation

Client-facing report that agencies can send directly to their customers.
Focuses on: revenue at risk, recoverable amounts, root causes, and recommended actions.
"""
from jinja2 import Template
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.discrepancy import Discrepancy, DiscrepancyStatus
from app.models.organization import Organization

REPORT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
<style>
@page { margin: 40px 50px; size: A4; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; color: #1a1a2e; font-size: 13px; line-height: 1.5; }
.cover { page-break-after: always; display: flex; flex-direction: column; justify-content: center; min-height: 700px; }
.cover-badge { display: inline-block; background: #e8f0fe; color: #1a56db; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; padding: 6px 16px; border-radius: 20px; margin-bottom: 24px; }
.cover h1 { font-size: 36px; font-weight: 700; color: #1a1a2e; margin: 0 0 8px 0; letter-spacing: -0.5px; }
.cover .subtitle { font-size: 18px; color: #6b7280; margin: 0 0 40px 0; }
.cover .client-info { font-size: 15px; color: #374151; margin-bottom: 48px; }
.cover .client-info strong { color: #1a1a2e; }
.metrics-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 0 0 48px 0; }
.metric-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; }
.metric-card.risk { border-left: 4px solid #dc2626; }
.metric-card.recoverable { border-left: 4px solid #059669; }
.metric-card.findings { border-left: 4px solid #d97706; }
.metric-card.action { border-left: 4px solid #2563eb; }
.metric-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #6b7280; margin-bottom: 4px; }
.metric-value { font-size: 28px; font-weight: 700; color: #1a1a2e; }
.metric-value.risk { color: #dc2626; }
.metric-value.green { color: #059669; }
.cover-footer { font-size: 11px; color: #9ca3af; margin-top: auto; }
h2 { font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 32px 0 16px 0; padding-bottom: 8px; border-bottom: 2px solid #e2e8f0; }
h3 { font-size: 16px; font-weight: 600; color: #374151; margin: 24px 0 8px 0; }
table { width: 100%; border-collapse: collapse; margin: 12px 0 24px 0; font-size: 12px; }
th { background: #1e293b; color: white; padding: 10px 12px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
th:first-child { border-radius: 6px 0 0 0; }
th:last-child { border-radius: 0 6px 0 0; }
td { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; }
tr:nth-child(even) { background: #f8fafc; }
.severity-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.severity-critical { background: #fef2f2; color: #991b1b; }
.severity-warning { background: #fffbeb; color: #92400e; }
.severity-info { background: #eff6ff; color: #1e40af; }
.finding-block { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 12px 0; page-break-inside: avoid; }
.finding-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.finding-title { font-weight: 600; font-size: 14px; color: #1e293b; }
.finding-amount { font-weight: 700; font-size: 16px; color: #dc2626; }
.finding-detail { margin: 8px 0; }
.finding-detail-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; font-weight: 600; margin-bottom: 2px; }
.finding-detail-text { font-size: 12px; color: #374151; }
.action-item { background: #eff6ff; border-left: 3px solid #2563eb; padding: 12px 16px; margin: 8px 0; border-radius: 0 6px 6px 0; page-break-inside: avoid; }
.action-priority { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; margin-bottom: 4px; }
.action-priority.high { color: #dc2626; }
.action-priority.medium { color: #d97706; }
.action-priority.low { color: #2563eb; }
.action-text { font-size: 12px; color: #1e293b; }
.action-impact { font-size: 11px; color: #6b7280; margin-top: 4px; }
.root-cause-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9; }
.root-cause-label { font-size: 13px; color: #374151; }
.root-cause-impact { font-size: 14px; font-weight: 600; color: #dc2626; }
.footer { font-size: 10px; color: #9ca3af; text-align: center; margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; }
</style>
</head>
<body>

<!-- COVER PAGE -->
<div class="cover">
  <span class="cover-badge">Client Revenue Risk Audit</span>
  <h1 style="font-size: 42px;">{{ agency_name }}</h1>
  <p class="subtitle" style="font-size: 24px;">Prepared for: <strong>{{ generated_for }}</strong></p>
  <div class="client-info">
    Audit Period: <strong>{{ audit_period }}</strong><br>
    Generated: <strong>{{ generated_date }}</strong>
  </div>

  <div class="metrics-row">
    <div class="metric-card risk">
      <div class="metric-label">Revenue At Risk</div>
      <div class="metric-value risk">${{ '{:,.2f}'.format(revenue_at_risk) }}</div>
    </div>
    <div class="metric-card recoverable">
      <div class="metric-label">Recoverable Revenue</div>
      <div class="metric-value green">${{ '{:,.2f}'.format(recoverable_revenue) }}</div>
    </div>
    <div class="metric-card" style="border-left: 4px solid #3b82f6;">
      <div class="metric-label">Annualized Recovery</div>
      <div class="metric-value" style="color: #2563eb;">${{ '{:,.2f}'.format(recoverable_revenue * 12) }}</div>
    </div>
    <div class="metric-card findings">
      <div class="metric-label">Critical Findings</div>
      <div class="metric-value">{{ critical_findings }}</div>
    </div>
  </div>

  {% if actions %}
  <div style="margin-top: 32px;">
    <h3 style="margin-top:0; font-size: 18px;">Top Recommended Actions</h3>
    {% for a in actions[:3] %}
    <div style="background: #eff6ff; border-left: 3px solid #2563eb; padding: 12px 16px; margin: 8px 0; border-radius: 0 6px 6px 0;">
      <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; color: #059669; margin-bottom: 4px;">Potential Recovery: ${{ '{:,.2f}'.format(a.impact) }}</div>
      <div style="font-size: 13px; color: #1e293b; font-weight: 500;">{{ a.action }}</div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <div class="cover-footer">
    Confidential — Prepared by {{ agency_name }} | {{ generated_date }}
  </div>
</div>

<!-- ISSUE BREAKDOWN -->
<h2>Financial Impact Breakdown</h2>
<table>
  <tr>
    <th>Issue Category</th>
    <th>Count</th>
    <th>Total Impact</th>
    <th>Recoverable</th>
  </tr>
  {% for b in impact_breakdown %}
  <tr>
    <td><strong>{{ b.label }}</strong></td>
    <td>{{ b.count }}</td>
    <td style="color: #dc2626; font-weight: 600;">${{ '{:,.2f}'.format(b.total_impact) }}</td>
    <td style="color: #059669; font-weight: 600;">${{ '{:,.2f}'.format(b.total_recoverable) }}</td>
  </tr>
  {% endfor %}
  <tr style="background: #1e293b; color: white; font-weight: 700;">
    <td>TOTAL</td>
    <td>{{ total_findings }}</td>
    <td>${{ '{:,.2f}'.format(revenue_at_risk) }}</td>
    <td>${{ '{:,.2f}'.format(recoverable_revenue) }}</td>
  </tr>
</table>

<!-- ROOT CAUSE ANALYSIS -->
<h2>Root Cause Analysis</h2>
{% for rc in root_causes %}
<div class="root-cause-item">
  <div>
    <div class="root-cause-label">{{ rc.cause }}</div>
    <div style="font-size: 11px; color: #9ca3af;">{{ rc.count }} occurrence{{ 's' if rc.count > 1 else '' }}</div>
  </div>
  <div class="root-cause-impact">${{ '{:,.2f}'.format(rc.total_impact) }}</div>
</div>
{% endfor %}

<!-- DETAILED FINDINGS -->
<h2>Detailed Findings</h2>
{% for f in findings %}
<div class="finding-block">
  <div class="finding-header">
    <div>
      <span class="severity-badge severity-{{ f.severity }}">{{ f.severity }}</span>
      <span class="finding-title" style="margin-left: 8px;">{{ f.label }}</span>
    </div>
    <div class="finding-amount">${{ '{:,.2f}'.format(f.amount) }}</div>
  </div>
  {% if f.customer_name %}<div style="font-size: 12px; color: #6b7280;">Customer: {{ f.customer_name }}</div>{% endif %}
  <div class="finding-detail">
    <div class="finding-detail-label">What Happened</div>
    <div class="finding-detail-text">{{ f.what_happened }}</div>
  </div>
  <div class="finding-detail">
    <div class="finding-detail-label">Why It Matters</div>
    <div class="finding-detail-text">{{ f.why_it_matters }}</div>
  </div>
  <div class="finding-detail">
    <div class="finding-detail-label">Recommended Action</div>
    <div class="finding-detail-text">{{ f.recommended_action }}</div>
  </div>
  <div style="display: flex; gap: 24px; margin-top: 8px; font-size: 11px;">
    <span>Impact: <strong style="color: #dc2626;">${{ '{:,.2f}'.format(f.financial_impact) }}</strong></span>
    <span>Recoverable: <strong style="color: #059669;">${{ '{:,.2f}'.format(f.recoverable_amount) }}</strong></span>
    {% if f.date %}<span>Date: {{ f.date }}</span>{% endif %}
  </div>
</div>
{% endfor %}

<!-- RECOMMENDED ACTIONS -->
<h2>Recommended Actions</h2>
{% for a in actions %}
<div class="action-item">
  <div class="action-priority {{ a.priority }}">{{ a.priority }} priority</div>
  <div class="action-text">{{ a.action }}</div>
  <div class="action-impact">Potential Recovery: ${{ '{:,.2f}'.format(a.impact) }}</div>
</div>
{% endfor %}

<div class="footer">
  <p>This report is for informational purposes. Always verify findings with your accounting records before taking action.</p>
</div>

</body>
</html>
'''

ISSUE_LABELS = {
    'missing_transaction': 'Missing Transaction',
    'duplicate_transaction': 'Duplicate Transaction',
    'refund_mismatch': 'Refund Mismatch',
    'chargeback_mismatch': 'Chargeback Not Recorded',
    'fee_variance': 'Processing Fee Variance',
    'revenue_leak': 'Revenue Leak',
    'payout_mismatch': 'Payout Mismatch',
}


def render_report_template(org: Organization, db: Session) -> str:
    """Render the report HTML content."""
    open_discs = db.query(Discrepancy).filter(
        Discrepancy.org_id == org.id,
        Discrepancy.status == DiscrepancyStatus.OPEN
    ).order_by(Discrepancy.amount.desc()).limit(50).all()

    from app.models.stripe_transaction import StripeTransaction

    # Compute metrics
    revenue_at_risk = sum(d.amount or 0 for d in open_discs)
    # Estimate recoverable: refunds & chargebacks are not recoverable
    non_recoverable_types = {'refund_mismatch', 'chargeback_mismatch'}
    recoverable = sum(
        d.amount or 0 for d in open_discs
        if d.issue_type.value not in non_recoverable_types
    )
    critical = sum(1 for d in open_discs if (d.confidence_score or 0) >= 0.90)

    # Build findings data
    findings = []
    for d in open_discs:
        is_recoverable = d.issue_type.value not in non_recoverable_types
        severity = 'critical' if (d.confidence_score or 0) >= 0.90 else 'warning' if (d.confidence_score or 0) >= 0.80 else 'info'
        findings.append({
            'label': ISSUE_LABELS.get(d.issue_type.value, d.issue_type.value),
            'severity': severity,
            'amount': d.amount or 0,
            'financial_impact': d.amount or 0,
            'recoverable_amount': (d.amount or 0) if is_recoverable else 0,
            'customer_name': d.customer_name,
            'date': d.date.strftime('%B %d, %Y') if d.date else None,
            'what_happened': d.suggested_cause or f'A {ISSUE_LABELS.get(d.issue_type.value, "discrepancy")} of ${d.amount or 0:,.2f} was detected.',
            'why_it_matters': _get_why_it_matters(d.issue_type.value, d.amount or 0),
            'recommended_action': _get_recommended_action(d),
        })

    # Impact breakdown
    breakdown = {}
    for f in findings:
        label = f['label']
        if label not in breakdown:
            breakdown[label] = {'label': label, 'count': 0, 'total_impact': 0, 'total_recoverable': 0}
        breakdown[label]['count'] += 1
        breakdown[label]['total_impact'] = round(breakdown[label]['total_impact'] + f['financial_impact'], 2)
        breakdown[label]['total_recoverable'] = round(breakdown[label]['total_recoverable'] + f['recoverable_amount'], 2)

    # Root causes
    cause_map = {}
    for d in open_discs:
        cause = _get_root_cause(d.issue_type.value)
        if cause not in cause_map:
            cause_map[cause] = {'cause': cause, 'count': 0, 'total_impact': 0}
        cause_map[cause]['count'] += 1
        cause_map[cause]['total_impact'] = round(cause_map[cause]['total_impact'] + (d.amount or 0), 2)
    root_causes = sorted(cause_map.values(), key=lambda x: x['total_impact'], reverse=True)

    # Actions
    actions = []
    for f in sorted(findings, key=lambda x: x['financial_impact'], reverse=True):
        severity = f['severity']
        actions.append({
            'priority': 'high' if severity == 'critical' else 'medium' if severity == 'warning' else 'low',
            'action': f['recommended_action'],
            'impact': f['financial_impact'],
        })

    html_content = Template(REPORT_TEMPLATE).render(
        agency_name='Bookkeeping Partners LLC',
        generated_for=org.name,
        audit_period='Last 90 Days',
        generated_date=datetime.utcnow().strftime('%B %d, %Y'),
        revenue_at_risk=revenue_at_risk,
        recoverable_revenue=recoverable,
        critical_findings=critical,
        action_count=len(actions),
        top_root_cause=root_causes[0]['cause'] if root_causes else None,
        impact_breakdown=list(breakdown.values()),
        total_findings=len(findings),
        root_causes=root_causes,
        findings=findings,
        actions=actions,
    )
    return html_content


def generate_report_pdf(org: Organization, db: Session) -> bytes:
    """Generate the Revenue Risk Audit PDF."""
    try:
        from weasyprint import HTML
    except Exception as e:
        raise RuntimeError(
            "PDF generation requires GTK3 runtime dependencies to be installed. "
            "Please follow the installation instructions for WeasyPrint."
        ) from e
    html_content = render_report_template(org, db)
    return HTML(string=html_content).write_pdf()


def _get_why_it_matters(issue_type: str, amount: float) -> str:
    messages = {
        'missing_transaction': f'Revenue is understated by ${amount:,.2f}. Financial statements may not reflect actual income, affecting tax filings and profitability reporting.',
        'duplicate_transaction': f'Revenue is overstated by ${amount:,.2f}. This creates a false picture of income and may result in overpaying taxes.',
        'refund_mismatch': f'Your books still show ${amount:,.2f} as earned revenue. This overstates income and could trigger audit findings.',
        'chargeback_mismatch': f'The ${amount:,.2f} chargeback loss is not reflected in financial statements, overstating revenue.',
        'fee_variance': f'Processing fees are ${amount:,.2f} higher than expected, reducing net revenue.',
        'revenue_leak': f'If payment was never collected, this represents ${amount:,.2f} of lost revenue.',
        'payout_mismatch': f'A ${amount:,.2f} payout discrepancy may indicate funds not properly settled.',
    }
    return messages.get(issue_type, f'This ${amount:,.2f} discrepancy needs investigation.')


def _get_root_cause(issue_type: str) -> str:
    causes = {
        'missing_transaction': 'Payment received outside normal invoicing workflow',
        'duplicate_transaction': 'Manual data entry resulted in duplicate record',
        'refund_mismatch': 'Refund processed in payment gateway but not recorded in accounting system',
        'chargeback_mismatch': 'Chargeback processed by payment gateway without accounting notification',
        'fee_variance': 'Processing fee rate differs from standard published rate',
        'revenue_leak': 'Payment gateway mismatch between Shopify and Stripe',
        'payout_mismatch': 'Bank settlement timing difference',
    }
    return causes.get(issue_type, 'Unidentified root cause')


def _get_recommended_action(d) -> str:
    if d.ai_explanation:
        return d.ai_explanation
    actions = {
        'missing_transaction': f'Review QuickBooks records for {d.date.strftime("%B %d, %Y") if d.date else "the transaction date"} and create a matching entry for ${d.amount or 0:,.2f} if missing.',
        'duplicate_transaction': f'Open QuickBooks and search for duplicate entries of ${d.amount or 0:,.2f}. Remove the incorrect duplicate.',
        'refund_mismatch': f'Create a Credit Memo in QuickBooks for ${d.amount or 0:,.2f}{" to " + d.customer_name if d.customer_name else ""}.',
        'chargeback_mismatch': f'Create a Journal Entry to record the chargeback loss of ${d.amount or 0:,.2f}. Debit chargeback expense, credit Accounts Receivable.',
        'fee_variance': f'Review your Stripe pricing plan. Compare actual fees against your negotiated rate for the ${d.amount or 0:,.2f} variance.',
        'revenue_leak': f'Verify payment status for the ${d.amount or 0:,.2f} order. If unpaid, initiate collection.',
    }
    return actions.get(d.issue_type.value, d.suggested_cause or 'Investigate this discrepancy.')
