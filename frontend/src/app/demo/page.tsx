'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

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
  stripe_ref: string | null
  shopify_ref: string | null
  qb_ref: string | null
}

interface AuditData {
  company: { name: string; audit_period: string }
  summary: {
    revenue_at_risk: number
    recoverable_revenue: number
    total_findings: number
    critical_findings: number
  }
  findings: Finding[]
  impact_breakdown: { issue_type: string; count: number; total_impact: number; total_recoverable: number }[]
  root_causes: { cause: string; count: number; total_impact: number }[]
  recommended_actions: { priority: string; action: string; impact: number }[]
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

// Fallback demo data so page works without backend running
const FALLBACK_DATA: AuditData = {
  company: { name: 'Acme Commerce Co.', audit_period: 'January 1 – March 31, 2024' },
  summary: { revenue_at_risk: 23421, recoverable_revenue: 14112, total_findings: 25, critical_findings: 9 },
  findings: [
    { id: 'f1', issue_type: 'missing_transaction', severity: 'critical', amount: 2400, financial_impact: 2400, recoverable_amount: 2400, customer_name: 'Sarah Mitchell', date: '2024-02-14', what_happened: 'A Stripe payment of $2,400.00 was received on February 14 but has no corresponding entry in QuickBooks.', why_it_matters: 'Revenue is understated by $2,400.00 in your books.', recommended_action: 'Create a matching Sales Receipt in QuickBooks for $2,400.00 dated February 14, 2024.', root_cause: 'Payment received outside normal invoicing workflow', confidence_score: 0.94, stripe_ref: 'ch_3PqR5s7t', shopify_ref: null, qb_ref: null },
    { id: 'f2', issue_type: 'refund_mismatch', severity: 'critical', amount: 3200, financial_impact: 3200, recoverable_amount: 0, customer_name: 'Elena Rodriguez', date: '2024-03-05', what_happened: 'A $3,200.00 refund was processed in Stripe but no credit memo exists in QuickBooks.', why_it_matters: 'Your books overstate revenue by $3,200.00.', recommended_action: 'Create a Credit Memo in QuickBooks for $3,200.00 to Elena Rodriguez.', root_cause: 'Refund processed in gateway but not in accounting', confidence_score: 0.96, stripe_ref: 'ch_7AbCdEf', shopify_ref: null, qb_ref: null },
    { id: 'f3', issue_type: 'duplicate_transaction', severity: 'critical', amount: 1850, financial_impact: 1850, recoverable_amount: 1850, customer_name: 'James Whitfield', date: '2024-01-22', what_happened: 'A QuickBooks payment for $1,850.00 appears twice on January 22.', why_it_matters: 'Revenue is overstated by $1,850.00 due to the duplicate.', recommended_action: 'Remove the duplicate QuickBooks entry.', root_cause: 'Manual data entry error', confidence_score: 0.92, stripe_ref: null, shopify_ref: null, qb_ref: 'QB-8847' },
    { id: 'f4', issue_type: 'revenue_leak', severity: 'critical', amount: 1200, financial_impact: 1200, recoverable_amount: 1200, customer_name: 'David Park', date: '2024-02-28', what_happened: 'Shopify order SH-44587 for $1,200.00 marked paid but no Stripe charge found.', why_it_matters: 'Payment may not have been collected — $1,200 potentially lost.', recommended_action: 'Verify payment and initiate collection if unpaid.', root_cause: 'Payment gateway mismatch', confidence_score: 0.88, stripe_ref: null, shopify_ref: 'SH-44587', qb_ref: null },
    { id: 'f5', issue_type: 'chargeback_mismatch', severity: 'critical', amount: 890, financial_impact: 890, recoverable_amount: 0, customer_name: 'Monica Chen', date: '2024-03-12', what_happened: 'A $890.00 chargeback in Stripe with no QuickBooks adjustment.', why_it_matters: 'Revenue is overstated by $890.00.', recommended_action: 'Create a Journal Entry to record the chargeback loss.', root_cause: 'Chargeback not synced to accounting', confidence_score: 0.91, stripe_ref: 'ch_9MnOpQr', shopify_ref: null, qb_ref: null },
    { id: 'f6', issue_type: 'revenue_leak', severity: 'warning', amount: 2150, financial_impact: 2150, recoverable_amount: 2150, customer_name: 'Priya Sharma', date: '2024-02-10', what_happened: 'Shopify order SH-44102 for $2,150 shows paid but no Stripe charge found.', why_it_matters: 'Potential $2,150 unrecovered revenue.', recommended_action: 'Verify payment and collect if outstanding.', root_cause: 'Payment gateway mismatch', confidence_score: 0.82, stripe_ref: null, shopify_ref: 'SH-44102', qb_ref: null },
    { id: 'f7', issue_type: 'missing_transaction', severity: 'warning', amount: 780, financial_impact: 780, recoverable_amount: 780, customer_name: 'Taylor Brooks', date: '2024-03-18', what_happened: 'A $780 Stripe payment from Taylor Brooks missing from QuickBooks.', why_it_matters: 'Revenue understated by $780.', recommended_action: 'Create a Sales Receipt in QuickBooks for $780.', root_cause: 'Payment outside invoicing workflow', confidence_score: 0.87, stripe_ref: 'ch_2YzAbCd', shopify_ref: null, qb_ref: null },
    { id: 'f8', issue_type: 'refund_mismatch', severity: 'warning', amount: 560, financial_impact: 560, recoverable_amount: 0, customer_name: 'Rachel Kim', date: '2024-02-20', what_happened: 'A $560 partial refund in Stripe not recorded in QuickBooks.', why_it_matters: 'Revenue overstated by $560.', recommended_action: 'Create a Credit Memo for $560.', root_cause: 'Refund not synced', confidence_score: 0.90, stripe_ref: 'ch_5WxYzAb', shopify_ref: null, qb_ref: null },
  ],
  impact_breakdown: [
    { issue_type: 'missing_transaction', count: 3, total_impact: 3630, total_recoverable: 3630 },
    { issue_type: 'refund_mismatch', count: 2, total_impact: 3760, total_recoverable: 0 },
    { issue_type: 'revenue_leak', count: 2, total_impact: 3350, total_recoverable: 3350 },
    { issue_type: 'duplicate_transaction', count: 2, total_impact: 2955, total_recoverable: 2955 },
    { issue_type: 'chargeback_mismatch', count: 1, total_impact: 890, total_recoverable: 0 },
    { issue_type: 'fee_variance', count: 2, total_impact: 235, total_recoverable: 235 },
  ],
  root_causes: [
    { cause: 'Refund processed in gateway but not in accounting', count: 2, total_impact: 3760 },
    { cause: 'Payment received outside normal invoicing workflow', count: 3, total_impact: 3630 },
    { cause: 'Payment gateway mismatch', count: 2, total_impact: 3350 },
    { cause: 'Manual data entry error', count: 2, total_impact: 2955 },
    { cause: 'Chargeback not synced to accounting', count: 1, total_impact: 890 },
  ],
  recommended_actions: [],
}

export default function DemoPage() {
  const [data, setData] = useState<AuditData>(FALLBACK_DATA)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'findings' | 'breakdown' | 'actions'>('findings')

  useEffect(() => {
    fetch(`${API_BASE}/demo/audit`)
      .then(r => r.json())
      .then(d => setData(d))
      .catch(() => {/* use fallback */})
  }, [])

  const fmt = (n: number) => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="bg-white border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center">
                <span className="text-white font-bold text-xs">R</span>
              </div>
              <span className="font-semibold text-gray-900">ReconFlow</span>
            </Link>
            <span className="text-gray-300">|</span>
            <span className="text-sm text-gray-500">Sample Revenue Risk Audit</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs bg-amber-100 text-amber-800 px-3 py-1 rounded-full font-medium">Demo Mode</span>
            <a href="mailto:debansh@reconflow.com?subject=Book%20a%20Demo" className="text-sm bg-emerald-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-emerald-700 transition">
              Book Demo
            </a>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-xs font-semibold uppercase tracking-widest text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full">Revenue Risk Audit</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-1">{data.company.name}</h1>
          <p className="text-gray-500">Audit Period: {data.company.audit_period}</p>
        </div>

        {/* Metric Cards — PHASE 3 metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="rf-metric-card rf-metric-card-risk">
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Revenue At Risk</div>
            <div className="text-3xl font-bold text-red-600 rf-number">${fmt(data.summary.revenue_at_risk)}</div>
          </div>
          <div className="rf-metric-card rf-metric-card-recover">
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Recoverable Revenue</div>
            <div className="text-3xl font-bold text-emerald-600 rf-number">${fmt(data.summary.recoverable_revenue)}</div>
          </div>
          <div className="rf-metric-card border-l-4 border-l-blue-500">
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Potential Client Value</div>
            <div className="text-3xl font-bold text-blue-600 rf-number">${fmt(data.summary.recoverable_revenue * 12)}</div>
            <div className="text-xs text-gray-500 mt-1">Annualized</div>
          </div>
          <div className="rf-metric-card rf-metric-card-findings">
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Critical Findings</div>
            <div className="text-3xl font-bold text-gray-900 rf-number">{data.summary.critical_findings}</div>
            <div className="text-xs text-gray-500 mt-1">{data.summary.total_findings} total</div>
          </div>
          <div className="rf-metric-card rf-metric-card-actions">
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Recommended Actions</div>
            <div className="text-3xl font-bold text-gray-900 rf-number">{data.findings.length}</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 p-1 rounded-xl mb-6 w-fit">
          {(['findings', 'breakdown', 'actions'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition ${activeTab === tab ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
            >
              {tab === 'findings' ? 'Findings' : tab === 'breakdown' ? 'Impact Breakdown' : 'Recommended Actions'}
            </button>
          ))}
        </div>

        {/* Findings Tab */}
        {activeTab === 'findings' && (
          <div className="space-y-3">
            {data.findings.map((f) => (
              <div key={f.id} className="rf-finding-block">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 min-w-0">
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full shrink-0 ${SEVERITY_STYLES[f.severity] || ''}`}>
                      {f.severity}
                    </span>
                    <div className="min-w-0">
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

                {/* Expandable details */}
                <button
                  onClick={() => setExpandedId(expandedId === f.id ? null : f.id)}
                  className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium transition"
                >
                  {expandedId === f.id ? 'Hide details ↑' : 'View details ↓'}
                </button>

                {expandedId === f.id && (
                  <div className="mt-4 space-y-4 pt-4 border-t border-gray-200">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">What Happened</div>
                      <div className="text-sm text-gray-700">{f.what_happened}</div>
                    </div>
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Why It Matters</div>
                      <div className="text-sm text-gray-700">{f.why_it_matters}</div>
                    </div>
                    <div className="bg-blue-50 border-l-3 border-blue-500 p-4 rounded-r-lg">
                      <div className="text-xs font-semibold uppercase tracking-wider text-blue-700 mb-1">Recommended Action</div>
                      {f.recoverable_amount > 0 && (
                        <div className="text-sm font-semibold text-emerald-700 mb-1">Potential Recovery: ${fmt(f.recoverable_amount)}</div>
                      )}
                      <div className="text-sm text-blue-900">{f.recommended_action}</div>
                    </div>
                    <details className="text-xs text-gray-400 mt-2">
                      <summary className="cursor-pointer mb-2 font-medium hover:text-gray-600 transition">Technical Details</summary>
                      <div className="flex gap-6 p-3 bg-gray-50 rounded-lg border border-gray-100">
                        {f.stripe_ref && <span>Stripe: {f.stripe_ref}</span>}
                        {f.shopify_ref && <span>Shopify: {f.shopify_ref}</span>}
                        {f.qb_ref && <span>QuickBooks: {f.qb_ref}</span>}
                      </div>
                    </details>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Breakdown Tab */}
        {activeTab === 'breakdown' && (
          <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b">
                  <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider text-gray-500">Issue Category</th>
                  <th className="text-center px-6 py-4 text-xs font-semibold uppercase tracking-wider text-gray-500">Count</th>
                  <th className="text-right px-6 py-4 text-xs font-semibold uppercase tracking-wider text-gray-500">Total Impact</th>
                  <th className="text-right px-6 py-4 text-xs font-semibold uppercase tracking-wider text-gray-500">Recoverable</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.impact_breakdown.map((b, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{ISSUE_LABELS[b.issue_type] || b.issue_type}</td>
                    <td className="px-6 py-4 text-sm text-center text-gray-600">{b.count}</td>
                    <td className="px-6 py-4 text-sm text-right font-semibold text-red-600">${fmt(b.total_impact)}</td>
                    <td className="px-6 py-4 text-sm text-right font-semibold text-emerald-600">${fmt(b.total_recoverable)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-gray-900 text-white font-semibold">
                  <td className="px-6 py-4 text-sm">Total</td>
                  <td className="px-6 py-4 text-sm text-center">{data.summary.total_findings}</td>
                  <td className="px-6 py-4 text-sm text-right">${fmt(data.summary.revenue_at_risk)}</td>
                  <td className="px-6 py-4 text-sm text-right">${fmt(data.summary.recoverable_revenue)}</td>
                </tr>
              </tfoot>
            </table>

            {/* Root Causes */}
            <div className="px-6 py-6 border-t">
              <h3 className="text-sm font-semibold text-gray-900 mb-4 uppercase tracking-wider">Root Causes</h3>
              <div className="space-y-3">
                {data.root_causes.map((rc, i) => (
                  <div key={i} className="flex items-center justify-between py-2">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-red-400" />
                      <span className="text-sm text-gray-700">{rc.cause}</span>
                      <span className="text-xs text-gray-400">{rc.count}×</span>
                    </div>
                    <span className="text-sm font-semibold text-red-600">${fmt(rc.total_impact)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Actions Tab */}
        {activeTab === 'actions' && (
          <div className="space-y-3">
            {data.findings
              .sort((a, b) => b.financial_impact - a.financial_impact)
              .map((f, i) => (
              <div key={f.id} className={`bg-white rounded-xl border p-5 ${i < data.summary.critical_findings ? 'border-l-4 border-l-red-500' : 'border-l-4 border-l-amber-400'}`}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-bold uppercase tracking-wider ${i < data.summary.critical_findings ? 'text-red-600' : 'text-amber-600'}`}>
                        {i < data.summary.critical_findings ? 'High Priority' : 'Medium Priority'}
                      </span>
                      <span className="text-xs text-gray-400">·</span>
                      <span className="text-xs text-gray-500">{ISSUE_LABELS[f.issue_type] || f.issue_type}</span>
                    </div>
                    <div className="text-sm text-gray-900 font-medium">{f.recommended_action}</div>
                    <div className="text-xs text-gray-500 mt-2">{f.customer_name}{f.date ? ` · ${f.date}` : ''}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-lg font-bold text-red-600">${fmt(f.financial_impact)}</div>
                    {f.recoverable_amount > 0 && (
                      <div className="text-xs text-emerald-600 font-medium">${fmt(f.recoverable_amount)} recoverable</div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* CTA */}
        <div className="mt-12 bg-slate-900 rounded-2xl p-10 text-center text-white">
          <h2 className="text-2xl font-bold mb-3">Ready to audit your own clients?</h2>
          <p className="text-gray-400 mb-6 max-w-xl mx-auto">
            This is a sample audit. Imagine running this for every client, every month — automatically.
          </p>
          <a href="mailto:debansh@reconflow.com?subject=Book%20a%20Demo" className="inline-flex items-center justify-center gap-2 bg-emerald-500 text-white font-semibold px-8 py-4 rounded-xl text-lg hover:bg-emerald-400 transition">
            Book a Demo
          </a>
        </div>
      </div>
    </div>
  )
}
