'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { reconciliation } from '@/lib/api'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Finding {
  id: string
  issue_type: string
  severity: string
  amount: number
  financial_impact: number
  recoverable_amount: number
  customer_name: string
  date: string
  what_happened: string
  why_it_matters: string
  recommended_action: string
  root_cause: string
  confidence_score: number
  ai_explanation?: string | null
}

interface ClientAuditData {
  client: { id: string; name: string; revenue_at_risk: number; recoverable_revenue: number; open_findings: number; critical_findings: number; last_audit: string }
  company: { name: string; audit_period: string }
  summary: { revenue_at_risk: number; recoverable_revenue: number; total_findings: number; critical_findings: number }
  findings: Finding[]
  impact_breakdown: { issue_type: string; count: number; total_impact: number; total_recoverable: number }[]
  root_causes: { cause: string; count: number; total_impact: number }[]
  recommended_actions: { priority: string; action: string; impact: number }[]
  trend: { direction: string; previous_risk: number; current_risk: number; change_pct: number }
}

const ISSUE_LABELS: Record<string, string> = {
  missing_transaction: 'Missing Transaction',
  duplicate_transaction: 'Duplicate Entry',
  refund_mismatch: 'Refund Not Recorded',
  chargeback_mismatch: 'Chargeback Missing',
  fee_variance: 'Fee Variance',
  revenue_leak: 'Revenue Leak',
}

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'rf-severity-critical',
  warning: 'rf-severity-warning',
  info: 'rf-severity-info',
}

const CLIENT_MAP: Record<string, { name: string; revenue_at_risk: number; recoverable_revenue: number; open_findings: number; critical_findings: number }> = {
  'client-001': { name: 'Acme Commerce Co.', revenue_at_risk: 14820, recoverable_revenue: 11640, open_findings: 12, critical_findings: 5 },
  'client-002': { name: 'Bloom & Vine Studio', revenue_at_risk: 8340, recoverable_revenue: 6120, open_findings: 8, critical_findings: 3 },
  'client-003': { name: 'NovaTech Solutions', revenue_at_risk: 22150, recoverable_revenue: 18400, open_findings: 15, critical_findings: 7 },
  'client-004': { name: 'Meridian Health Supply', revenue_at_risk: 5670, recoverable_revenue: 4200, open_findings: 6, critical_findings: 2 },
  'client-005': { name: 'Peak Performance Gear', revenue_at_risk: 31200, recoverable_revenue: 24800, open_findings: 18, critical_findings: 9 },
}

const FALLBACK_FINDINGS: Finding[] = [
  { id: 'f1', issue_type: 'missing_transaction', severity: 'critical', amount: 2400, financial_impact: 2400, recoverable_amount: 2400, customer_name: 'Sarah Mitchell', date: '2024-02-14', what_happened: 'A Stripe payment of $2,400.00 was received on February 14 but has no corresponding entry in QuickBooks.', why_it_matters: 'Revenue is understated by $2,400.00, affecting tax filings and profitability reporting.', recommended_action: 'Create a matching Sales Receipt in QuickBooks for $2,400.00 dated February 14, 2024.', root_cause: 'Payment received outside normal invoicing workflow', confidence_score: 0 },
  { id: 'f2', issue_type: 'refund_mismatch', severity: 'critical', amount: 3200, financial_impact: 3200, recoverable_amount: 0, customer_name: 'Elena Rodriguez', date: '2024-03-05', what_happened: 'A $3,200.00 refund was processed in Stripe but no credit memo exists in QuickBooks.', why_it_matters: 'Your books overstate revenue by $3,200.00. This could trigger audit findings.', recommended_action: 'Create a Credit Memo in QuickBooks for $3,200.00 to Elena Rodriguez dated March 5, 2024.', root_cause: 'Refund processed in gateway but not in accounting', confidence_score: 0 },
  { id: 'f3', issue_type: 'duplicate_transaction', severity: 'critical', amount: 1850, financial_impact: 1850, recoverable_amount: 1850, customer_name: 'James Whitfield', date: '2024-01-22', what_happened: 'A QuickBooks payment for $1,850.00 appears twice on January 22.', why_it_matters: 'Revenue is overstated by $1,850.00 due to the duplicate, which may result in overpaying taxes.', recommended_action: 'Remove the duplicate QuickBooks entry and verify the remaining entry matches the Stripe charge.', root_cause: 'Manual data entry error', confidence_score: 0 },
  { id: 'f4', issue_type: 'revenue_leak', severity: 'critical', amount: 1200, financial_impact: 1200, recoverable_amount: 1200, customer_name: 'David Park', date: '2024-02-28', what_happened: 'Shopify order SH-44587 for $1,200.00 marked paid but no Stripe charge found.', why_it_matters: 'Payment may not have been collected — $1,200 potentially lost.', recommended_action: 'Verify payment status and initiate collection if unpaid.', root_cause: 'Payment gateway mismatch', confidence_score: 0 },
  { id: 'f5', issue_type: 'chargeback_mismatch', severity: 'critical', amount: 890, financial_impact: 890, recoverable_amount: 0, customer_name: 'Monica Chen', date: '2024-03-12', what_happened: 'A $890.00 chargeback in Stripe with no QuickBooks adjustment.', why_it_matters: 'Revenue is overstated by $890.00. The lost funds are not reflected in statements.', recommended_action: 'Create a Journal Entry to record the chargeback loss of $890.00.', root_cause: 'Chargeback not synced to accounting', confidence_score: 0 },
  { id: 'f6', issue_type: 'revenue_leak', severity: 'warning', amount: 2150, financial_impact: 2150, recoverable_amount: 2150, customer_name: 'Priya Sharma', date: '2024-02-10', what_happened: 'Shopify order SH-44102 for $2,150 shows paid but no Stripe charge found.', why_it_matters: 'Potential $2,150 unrecovered revenue.', recommended_action: 'Verify payment and collect if outstanding.', root_cause: 'Payment gateway mismatch', confidence_score: 0 },
  { id: 'f7', issue_type: 'missing_transaction', severity: 'warning', amount: 780, financial_impact: 780, recoverable_amount: 780, customer_name: 'Taylor Brooks', date: '2024-03-18', what_happened: 'A $780 Stripe payment from Taylor Brooks missing from QuickBooks.', why_it_matters: 'Revenue understated by $780.', recommended_action: 'Create a Sales Receipt in QuickBooks for $780.', root_cause: 'Payment outside invoicing workflow', confidence_score: 0 },
  { id: 'f8', issue_type: 'refund_mismatch', severity: 'warning', amount: 560, financial_impact: 560, recoverable_amount: 0, customer_name: 'Rachel Kim', date: '2024-02-20', what_happened: 'A $560 partial refund in Stripe not recorded in QuickBooks.', why_it_matters: 'Revenue overstated by $560.', recommended_action: 'Create a Credit Memo for $560 to Rachel Kim.', root_cause: 'Refund not synced', confidence_score: 0 },
]

function buildFallback(clientId: string): ClientAuditData {
  const client = CLIENT_MAP[clientId] || CLIENT_MAP['client-001']
  const findings = FALLBACK_FINDINGS.slice(0, client.open_findings)
  return {
    client: { id: clientId, ...client, last_audit: '2024-03-28' },
    company: { name: client.name, audit_period: 'January 1 – March 31, 2024' },
    summary: { revenue_at_risk: client.revenue_at_risk, recoverable_revenue: client.recoverable_revenue, total_findings: client.open_findings, critical_findings: client.critical_findings },
    findings,
    impact_breakdown: [
      { issue_type: 'missing_transaction', count: 2, total_impact: 3180, total_recoverable: 3180 },
      { issue_type: 'refund_mismatch', count: 2, total_impact: 3760, total_recoverable: 0 },
      { issue_type: 'revenue_leak', count: 2, total_impact: 3350, total_recoverable: 3350 },
      { issue_type: 'duplicate_transaction', count: 1, total_impact: 1850, total_recoverable: 1850 },
      { issue_type: 'chargeback_mismatch', count: 1, total_impact: 890, total_recoverable: 0 },
    ],
    root_causes: [
      { cause: 'Refund processed in gateway but not in accounting', count: 2, total_impact: 3760 },
      { cause: 'Payment gateway mismatch between Shopify and Stripe', count: 2, total_impact: 3350 },
      { cause: 'Payment received outside normal invoicing workflow', count: 2, total_impact: 3180 },
      { cause: 'Manual data entry error', count: 1, total_impact: 1850 },
      { cause: 'Chargeback not synced to accounting', count: 1, total_impact: 890 },
    ],
    recommended_actions: [],
    trend: { direction: 'improving', previous_risk: client.revenue_at_risk * 1.15, current_risk: client.revenue_at_risk, change_pct: -13.0 },
  }
}

export default function ClientAuditPage() {
  const params = useParams()
  const clientId = params.id as string
  const [data, setData] = useState<ClientAuditData>(buildFallback(clientId))
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [explainingId, setExplainingId] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('rf_token')
    const headers: Record<string, string> = {}
    if (token) headers['Authorization'] = `Bearer ${token}`

    const url = clientId === 'real-org'
      ? `${API_BASE}/discrepancies/audit`
      : `${API_BASE}/demo/client/${clientId}`

    fetch(url, { headers })
      .then(r => {
        if (!r.ok) throw new Error('API failed')
        return r.json()
      })
      .then(d => setData(d))
      .catch(() => { setData(buildFallback(clientId)) })
  }, [clientId])

  const handleExplain = async (discId: string) => {
    setExplainingId(discId)
    try {
      const res = await reconciliation.explain(discId)
      setData(prev => {
        const updatedFindings = prev.findings.map(f => {
          if (f.id === discId) {
            return { ...f, ai_explanation: res.data.explanation }
          }
          return f
        })
        return { ...prev, findings: updatedFindings }
      })
    } catch (e) {
      console.error(e)
    }
    setExplainingId(null)
  }

  const fmt = (n: number) => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="bg-white border-b sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/agency" className="flex items-center gap-2 text-gray-500 hover:text-gray-700 transition">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
              <span className="text-sm font-medium">Back to Clients</span>
            </Link>
            <span className="text-gray-300">|</span>
            <span className="text-sm text-gray-500">Revenue Risk Audit</span>
          </div>
          <div className="flex items-center gap-3">
            <button className="text-sm text-gray-600 hover:text-gray-900 font-medium px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              Export PDF
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-10">

        {/* DELIVERABLE HEADER — This looks like a report, not a dashboard */}
        <div className="bg-white rounded-2xl border overflow-hidden mb-8">
          {/* Dark header band */}
          <div className="bg-slate-900 px-10 py-8 text-white">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-xs font-semibold uppercase tracking-[3px] text-emerald-400 mb-2">Revenue Risk Audit</div>
                <h1 className="text-3xl font-bold mb-1">{data.client.name}</h1>
                <div className="text-sm text-gray-400">{data.company.audit_period}</div>
              </div>
              <div className="text-right">
                {data.trend && (
                  <div className={`inline-flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-full ${data.trend.change_pct < 0 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'}`}>
                    {data.trend.change_pct < 0 ? '↓' : '↑'} {Math.abs(data.trend.change_pct)}% vs last period
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-4 divide-x border-t border-gray-100">
            <div className="px-8 py-6 text-center">
              <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Revenue At Risk</div>
              <div className="text-3xl font-bold text-red-600">${fmt(data.summary.revenue_at_risk)}</div>
            </div>
            <div className="px-8 py-6 text-center">
              <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Recoverable Revenue</div>
              <div className="text-3xl font-bold text-emerald-600">${fmt(data.summary.recoverable_revenue)}</div>
            </div>
            <div className="px-8 py-6 text-center bg-blue-50/50">
              <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Potential Annual Recovery</div>
              <div className="text-3xl font-bold text-blue-600">${fmt(data.summary.recoverable_revenue * 12)}</div>
            </div>
            <div className="px-8 py-6 text-center">
              <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Critical Findings</div>
              <div className="text-3xl font-bold text-gray-900">{data.summary.critical_findings}</div>
              <div className="text-xs text-gray-500 mt-1">{data.summary.total_findings} total</div>
            </div>
          </div>
        </div>

        {/* Immediate Actions */}
        <div className="bg-white rounded-xl border p-6 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Top 3 Recommended Actions</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {data.findings.filter(f => f.recoverable_amount > 0).slice(0, 3).map(f => (
              <div key={`action-${f.id}`} className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
                <div className="text-xs font-bold text-emerald-600 uppercase mb-1">Potential Recovery: ${fmt(f.recoverable_amount)}</div>
                <div className="text-sm font-medium text-blue-900">{f.recommended_action}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-3 gap-8">
            {/* Root Cause Summary */}
            <div className="grid md:grid-cols-2 gap-8 mb-8">
              <div className="bg-white rounded-xl border p-6">
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">Financial Impact</h3>
                <div className="space-y-3">
                  {data.impact_breakdown.map((b, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                      <div>
                        <div className="text-sm text-gray-700">{ISSUE_LABELS[b.issue_type] || b.issue_type}</div>
                        <div className="text-xs text-gray-400">{b.count} issue{b.count > 1 ? 's' : ''}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold text-red-600">${fmt(b.total_impact)}</div>
                        {b.total_recoverable > 0 && (
                          <div className="text-xs text-emerald-600">${fmt(b.total_recoverable)} rec.</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-xl border p-6">
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">Root Causes</h3>
                <div className="space-y-3">
                  {data.root_causes.map((rc, i) => (
                    <div key={i} className="flex items-start gap-3 py-2 border-b border-gray-100 last:border-0">
                      <div className="w-5 h-5 rounded-full bg-red-100 flex items-center justify-center shrink-0 mt-0.5">
                        <span className="text-xs text-red-600 font-bold">{i + 1}</span>
                      </div>
                      <div>
                        <div className="text-sm text-gray-700">{rc.cause}</div>
                        <div className="text-xs text-gray-400">{rc.count} occurrence{rc.count > 1 ? 's' : ''} · ${fmt(rc.total_impact)} impact</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

          {/* Right column — Summary sidebar */}
          <div className="space-y-6">

            {/* Detailed Findings */}
            <div>
              <h2 className="text-lg font-bold text-gray-900 mb-4">Detailed Findings</h2>
              <div className="space-y-3">
                {data.findings.map(f => (
                  <div key={f.id} className="bg-white rounded-xl border p-5 hover:shadow-sm transition">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full shrink-0 ${SEVERITY_STYLES[f.severity] || ''}`}>
                          {f.severity}
                        </span>
                        <div>
                          <div className="font-semibold text-gray-900">{ISSUE_LABELS[f.issue_type] || f.issue_type}</div>
                          <div className="text-sm text-gray-500 mt-0.5">
                            {f.customer_name}{f.date ? ` · ${new Date(f.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}` : ''}
                          </div>
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-lg font-bold text-red-600">${fmt(f.financial_impact)}</div>
                        {f.recoverable_amount > 0 && (
                          <div className="text-xs text-emerald-600 font-medium">${fmt(f.recoverable_amount)} recoverable</div>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={() => setExpandedId(expandedId === f.id ? null : f.id)}
                      className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium"
                    >
                      {expandedId === f.id ? 'Hide details ↑' : 'View details ↓'}
                    </button>

                    {expandedId === f.id && (
                      <div className="mt-4 space-y-4 pt-4 border-t">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">What Happened</div>
                          <div className="text-sm text-gray-700">{f.what_happened}</div>
                        </div>
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Why It Matters</div>
                          <div className="text-sm text-gray-700">{f.why_it_matters}</div>
                        </div>
                        {f.ai_explanation ? (
                          <div className="bg-emerald-50 border-l-4 border-emerald-500 p-4 rounded-r-lg">
                            <div className="text-xs font-semibold uppercase tracking-wider text-emerald-700 mb-1 flex items-center gap-1">
                              <span>✨ AI Insight</span>
                            </div>
                            <div className="text-sm text-emerald-900 mt-1">{f.ai_explanation}</div>
                          </div>
                        ) : (
                          <button
                            onClick={() => handleExplain(f.id)}
                            disabled={explainingId === f.id}
                            className="w-full text-xs bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-2"
                          >
                            ✨ {explainingId === f.id ? 'Analyzing discrepancy...' : 'Explain finding with AI'}
                          </button>
                        )}
                        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
                          <div className="text-xs font-semibold uppercase tracking-wider text-blue-700 mb-1">Recommended Action</div>
                          <div className="text-sm text-emerald-700 mb-1 font-semibold">Potential Recovery: ${fmt(f.recoverable_amount)}</div>
                          <div className="text-sm text-blue-900">{f.recommended_action}</div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Trend */}
            {data.trend && (
              <div className="bg-white rounded-xl border p-6">
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">Trend</h3>
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${data.trend.change_pct < 0 ? 'bg-emerald-100' : 'bg-red-100'}`}>
                    <span className={`text-lg ${data.trend.change_pct < 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                      {data.trend.change_pct < 0 ? '↓' : '↑'}
                    </span>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      Risk {data.trend.direction === 'improving' ? 'decreased' : 'increased'} {Math.abs(data.trend.change_pct)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      ${fmt(data.trend.previous_risk)} → ${fmt(data.trend.current_risk)}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
