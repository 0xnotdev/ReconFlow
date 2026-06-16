import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, 
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

def add_header_footer(canvas_obj, doc):
    canvas_obj.saveState()
    # Footer
    canvas_obj.setFont('Helvetica', 9)
    canvas_obj.setFillColor(colors.HexColor('#64748b'))
    canvas_obj.drawString(50, 40, "Confidential - Acme Commerce Co.")
    canvas_obj.drawRightString(A4[0] - 50, 40, f"Page {doc.page}")
    
    # Header line
    if doc.page > 1:
        canvas_obj.setStrokeColor(colors.HexColor('#cbd5e1'))
        canvas_obj.setLineWidth(1)
        canvas_obj.line(50, A4[1] - 50, A4[0] - 50, A4[1] - 50)
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(colors.HexColor('#0f172a'))
        canvas_obj.drawString(50, A4[1] - 40, "ReconFlow")
        canvas_obj.drawRightString(A4[0] - 50, A4[1] - 40, "Revenue Intelligence Audit")
    
    canvas_obj.restoreState()

def generate_professional_pdf(filename):
    doc = BaseDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=70, bottomMargin=70)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='test', frames=frame, onPage=add_header_footer)
    doc.addPageTemplates([template])
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'MainTitle', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=36, leading=42, textColor=colors.HexColor('#ffffff'), alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'SubTitle', parent=styles['Normal'], fontName='Helvetica',
        fontSize=18, leading=24, textColor=colors.HexColor('#cbd5e1'), alignment=TA_CENTER
    )
    h1_style = ParagraphStyle(
        'H1', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=20, leading=26, textColor=colors.HexColor('#0f172a'), spaceAfter=16
    )
    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=14, leading=18, textColor=colors.HexColor('#1e293b'), spaceAfter=10, spaceBefore=16
    )
    normal_style = ParagraphStyle(
        'CustomNormal', parent=styles['Normal'], fontName='Helvetica',
        fontSize=11, leading=16, textColor=colors.HexColor('#334155'), alignment=TA_JUSTIFY, spaceAfter=10
    )
    metric_label_style = ParagraphStyle(
        'MetricLabel', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#64748b'), alignment=TA_CENTER
    )
    metric_val_risk = ParagraphStyle(
        'MetricValRisk', fontName='Helvetica-Bold', fontSize=24, textColor=colors.HexColor('#dc2626'), alignment=TA_CENTER
    )
    metric_val_success = ParagraphStyle(
        'MetricValSuccess', fontName='Helvetica-Bold', fontSize=24, textColor=colors.HexColor('#059669'), alignment=TA_CENTER
    )
    
    elements = []
    
    # ---------------------------------------------------------
    # COVER PAGE
    # ---------------------------------------------------------
    # We use a Table to create a big colored block for the cover
    cover_data = [
        [Spacer(1, 150)],
        [Paragraph("FINANCIAL DISCREPANCY", subtitle_style)],
        [Paragraph("& REVENUE RISK AUDIT", title_style)],
        [Spacer(1, 40)],
        [Paragraph("PREPARED FOR", ParagraphStyle('CP', fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER, spaceAfter=4))],
        [Spacer(1, 10)],
        [Paragraph("Acme Commerce Co.", ParagraphStyle('CC', fontName='Helvetica-Bold', fontSize=28, leading=34, textColor=colors.white, alignment=TA_CENTER, spaceAfter=8))],
        [Spacer(1, 30)],
        [Paragraph("Prepared by ReconFlow AI Auditors", subtitle_style)],
        [Spacer(1, 10)],
        [Paragraph(f"Date: {datetime.date.today().strftime('%B %d, %Y')}", subtitle_style)],
        [Spacer(1, 200)]
    ]
    cover_table = Table(cover_data, colWidths=[doc.width])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0f172a')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    
    elements.append(cover_table)
    elements.append(PageBreak())
    
    # ---------------------------------------------------------
    # EXECUTIVE SUMMARY
    # ---------------------------------------------------------
    elements.append(Paragraph("Executive Summary", h1_style))
    elements.append(Paragraph(
        "This audit was conducted by ReconFlow's AI-driven reconciliation engine. We analyzed over 15,400 transactions "
        "across Stripe, Shopify, and QuickBooks for the period of January 1, 2024 to March 31, 2024. The objective of "
        "this audit is to identify unrecorded revenue, missing payouts, duplicated accounting entries, and general financial "
        "discrepancies that pose a risk to the financial integrity and cash flow of Acme Commerce Co.", 
        normal_style
    ))
    elements.append(Spacer(1, 10))
    
    # Key Metrics Grid
    metrics_data = [
        [
            Paragraph("REVENUE AT RISK", metric_label_style),
            Paragraph("RECOVERABLE REVENUE", metric_label_style),
            Paragraph("CRITICAL FINDINGS", metric_label_style)
        ],
        [
            Paragraph("$14,820.00", metric_val_risk),
            Paragraph("$11,640.00", metric_val_success),
            Paragraph("12", metric_val_risk)
        ]
    ]
    metrics_table = Table(metrics_data, colWidths=[doc.width/3.0]*3)
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 16),
        ('BOTTOMPADDING', (0,0), (-1,-1), 16),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph(
        "<b>High-Level Impact:</b> The total identified revenue at risk represents approximately 1.2% of gross processing volume "
        "for the period. Of the $14,820 identified, $11,640 is fully recoverable through immediate administrative action "
        "(e.g., matching unrecorded Stripe payments or collecting on unpaid invoices). The remaining $3,180 consists of unrecorded "
        "refunds and chargebacks which overstate current revenue but are non-recoverable.",
        normal_style
    ))
    elements.append(Spacer(1, 10))
    
    # Methodology Table
    elements.append(Paragraph("Data Sources Analyzed", h2_style))
    sources_data = [
        ["System", "Record Type", "Volume Analyzed"],
        ["Stripe", "Charges, Refunds, Disputes, Payouts", "15,402 records"],
        ["Shopify", "Orders, Fulfillments", "14,890 records"],
        ["QuickBooks", "Invoices, Sales Receipts, Journal Entries", "15,310 records"]
    ]
    t_sources = Table(sources_data, colWidths=[150, 200, 140])
    t_sources.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    elements.append(t_sources)
    
    elements.append(PageBreak())
    
    # ---------------------------------------------------------
    # DETAILED FINDINGS
    # ---------------------------------------------------------
    elements.append(Paragraph("Detailed Discrepancy Findings", h1_style))
    elements.append(Paragraph(
        "The following section details the most critical discrepancies identified by the matching engine. Each finding "
        "includes financial impact analysis, root cause categorization, and recommended remediation steps.",
        normal_style
    ))
    elements.append(Spacer(1, 10))
    
    findings = [
        {
            "id": "AUDIT-001", "type": "Missing Transaction (Revenue Leak)", "severity": "CRITICAL", 
            "amount": "$2,400.00", "recoverable": "Yes ($2,400.00)", "date": "Feb 14, 2024", "customer": "Sarah Mitchell",
            "desc": "A finalized payment of $2,400.00 was processed via Stripe (ch_3Oabcd123) on February 14th, but no corresponding Sales Receipt or Invoice was found in QuickBooks.",
            "cause": "Payment received outside normal invoicing workflow, likely a manual invoice link sent directly to the customer.",
            "action": "Create a matching Sales Receipt in QuickBooks for $2,400.00 dated February 14, 2024, mapped to the primary Stripe clearing account."
        },
        {
            "id": "AUDIT-002", "type": "Refund Mismatch", "severity": "HIGH", 
            "amount": "$3,200.00", "recoverable": "No", "date": "Mar 05, 2024", "customer": "Elena Rodriguez",
            "desc": "A full refund of $3,200.00 was issued via the Stripe dashboard for order SH-44910. However, the original invoice remains fully paid in QuickBooks with no Credit Memo applied.",
            "cause": "Refund processed directly in the payment gateway rather than initiating the refund through the accounting or e-commerce platform.",
            "action": "Create a Credit Memo in QuickBooks for $3,200.00 to Elena Rodriguez dated March 5, 2024, to accurately reflect the reduction in revenue."
        },
        {
            "id": "AUDIT-003", "type": "Duplicate Accounting Entry", "severity": "CRITICAL", 
            "amount": "$1,850.00", "recoverable": "Yes ($1,850.00 tax savings)", "date": "Jan 22, 2024", "customer": "James Whitfield",
            "desc": "Two identical QuickBooks Sales Receipts for $1,850.00 exist on January 22 for the same customer, but only one corresponding charge exists in Stripe.",
            "cause": "Manual data entry error or sync tool glitch resulting in a duplicated record.",
            "action": "Void or delete the duplicate QuickBooks entry (TxnID: 9482) and verify the remaining entry properly matches the Stripe charge."
        },
        {
            "id": "AUDIT-004", "type": "Uncollected E-commerce Order", "severity": "CRITICAL", 
            "amount": "$1,200.00", "recoverable": "Yes ($1,200.00)", "date": "Feb 28, 2024", "customer": "David Park",
            "desc": "Shopify order SH-44587 for $1,200.00 is marked as 'Paid' and 'Fulfilled', but no matching charge was successfully captured in Stripe.",
            "cause": "Payment gateway timeout or authorization failure that was incorrectly synced as a successful payment back to Shopify.",
            "action": "Contact the customer to collect the $1,200.00 payment, as the goods have already been fulfilled without actual fund capture."
        },
        {
            "id": "AUDIT-005", "type": "Unrecorded Chargeback", "severity": "HIGH", 
            "amount": "$890.00", "recoverable": "No", "date": "Mar 12, 2024", "customer": "Monica Chen",
            "desc": "A chargeback of $890.00 was lost in Stripe, and the funds were deducted from the account balance. No adjustment exists in QuickBooks.",
            "cause": "Dispute lost in gateway. Lack of automated webhook integration for dispute events into the accounting ledger.",
            "action": "Record a Journal Entry for $890.00 crediting Accounts Receivable and debiting Chargeback Expense, dated March 12."
        }
    ]
    
    for f in findings:
        # Create a stylized card for each finding using a Table
        header_color = colors.HexColor('#dc2626') if f['severity'] == 'CRITICAL' else colors.HexColor('#d97706')
        
        card_data = [
            [
                Paragraph(f"<b>{f['id']} | {f['type']}</b>", ParagraphStyle('CardTitle', fontName='Helvetica-Bold', fontSize=12, textColor=colors.white)),
                Paragraph(f"<b>{f['severity']}</b>", ParagraphStyle('CardSev', fontName='Helvetica-Bold', fontSize=10, textColor=colors.white, alignment=TA_RIGHT))
            ],
            [
                Paragraph("<b>Financial Impact:</b>", ParagraphStyle('lbl', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#475569'))),
                Paragraph(f"<font color='red'>{f['amount']}</font> (Recoverable: {f['recoverable']})", normal_style)
            ],
            [
                Paragraph("<b>Transaction Info:</b>", ParagraphStyle('lbl', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#475569'))),
                Paragraph(f"{f['date']} | Customer: {f['customer']}", normal_style)
            ],
            [
                Paragraph("<b>Description:</b>", ParagraphStyle('lbl', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#475569'))),
                Paragraph(f['desc'], normal_style)
            ],
            [
                Paragraph("<b>Root Cause:</b>", ParagraphStyle('lbl', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#475569'))),
                Paragraph(f['cause'], normal_style)
            ],
            [
                Paragraph("<b>Action Required:</b>", ParagraphStyle('lbl', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#475569'))),
                Paragraph(f"<b>{f['action']}</b>", ParagraphStyle('act', fontName='Helvetica', fontSize=11, textColor=colors.HexColor('#0f172a')))
            ]
        ]
        
        t_card = Table(card_data, colWidths=[120, doc.width-120])
        t_card.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), header_color),
            ('BOTTOMPADDING', (0,0), (1,0), 6),
            ('TOPPADDING', (0,0), (1,0), 6),
            ('SPAN', (1,1), (1,1)),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,1), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0,1), (0,-1), colors.HexColor('#f8fafc')),
            ('PADDING', (0,1), (-1,-1), 8),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ]))
        
        elements.append(KeepTogether(t_card))
        elements.append(Spacer(1, 20))
        
    elements.append(PageBreak())
    
    # ---------------------------------------------------------
    # CONCLUSION & NEXT STEPS
    # ---------------------------------------------------------
    elements.append(Paragraph("Strategic Recommendations", h1_style))
    elements.append(Paragraph(
        "Based on the root causes identified across the discrepancies, ReconFlow recommends implementing the following "
        "process improvements to prevent future revenue leakage:",
        normal_style
    ))
    
    recs = [
        "<b>1. Unify Payment Workflows:</b> Avoid processing manual payments or refunds directly in the Stripe dashboard. Initiate all financial actions from Shopify or QuickBooks to ensure proper downstream syncing.",
        "<b>2. Implement Dispute Tracking:</b> Establish a standard operating procedure for recording chargebacks in QuickBooks immediately upon receipt of a dispute notification from the payment processor.",
        "<b>3. Monthly Automated Audits:</b> The volume of transactions makes manual reconciliation error-prone. Run the ReconFlow automated matching engine at the close of every month prior to finalizing financial statements."
    ]
    
    for r in recs:
        elements.append(Paragraph(r, normal_style))
        elements.append(Spacer(1, 5))
        
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("<b>End of Report</b>", ParagraphStyle('End', fontName='Helvetica-Bold', fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor('#94a3b8'))))
    
    doc.build(elements)
    print("Professional PDF generated successfully.")

if __name__ == "__main__":
    import sys
    output_path = r"d:\ReconFlow\frontend\public\sample-audit.pdf"
    generate_professional_pdf(output_path)
