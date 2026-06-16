import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.pdf_service import REPORT_TEMPLATE
from datetime import datetime
from jinja2 import Template
from weasyprint import HTML

# Dummy data from demo client Acme Commerce Co.
agency_name = 'ReconFlow Bookkeeping'
generated_for = 'Acme Commerce Co.'
audit_period = 'January 1 – March 31, 2024'
generated_date = datetime.utcnow().strftime('%B %d, %Y')
revenue_at_risk = 14820.0
recoverable_revenue = 11640.0
critical_findings = 5
action_count = 12

actions = [
    {"action": "Create Sales Receipt for missing Stripe payment", "impact": 2400.0, "priority": "high"},
    {"action": "Create Credit Memo for missing refund", "impact": 3200.0, "priority": "high"},
    {"action": "Verify Shopify order payment collection", "impact": 1200.0, "priority": "high"},
]

impact_breakdown = [
    {"label": "Missing Transaction", "count": 2, "total_impact": 3180.0, "total_recoverable": 3180.0},
    {"label": "Refund Mismatch", "count": 2, "total_impact": 3760.0, "total_recoverable": 0.0},
    {"label": "Revenue Leak", "count": 2, "total_impact": 3350.0, "total_recoverable": 3350.0},
]

root_causes = [
    {"cause": "Refund processed in gateway but not in accounting", "count": 2, "total_impact": 3760.0},
    {"cause": "Payment gateway mismatch between Shopify and Stripe", "count": 2, "total_impact": 3350.0},
]

findings = [
    {
        "label": "Missing Transaction",
        "severity": "critical",
        "amount": 2400.0,
        "financial_impact": 2400.0,
        "recoverable_amount": 2400.0,
        "customer_name": "Sarah Mitchell",
        "what_happened": "A Stripe payment of $2,400.00 was received on February 14 but has no corresponding entry in QuickBooks.",
        "why_it_matters": "Revenue is understated by $2,400.00, affecting tax filings and profitability reporting.",
        "recommended_action": "Create a matching Sales Receipt in QuickBooks for $2,400.00 dated February 14, 2024.",
        "date": "2024-02-14"
    }
]

html_content = Template(REPORT_TEMPLATE).render(
    agency_name=agency_name,
    generated_for=generated_for,
    audit_period=audit_period,
    generated_date=generated_date,
    revenue_at_risk=revenue_at_risk,
    recoverable_revenue=recoverable_revenue,
    critical_findings=critical_findings,
    action_count=action_count,
    top_root_cause=root_causes[0]['cause'],
    impact_breakdown=impact_breakdown,
    total_findings=action_count,
    root_causes=root_causes,
    findings=findings,
    actions=actions
)

output_path = os.path.join(os.path.dirname(__file__), '../../frontend/public/sample-audit.pdf')
HTML(string=html_content).write_pdf(output_path)
print("Successfully generated sample audit PDF at:", output_path)
