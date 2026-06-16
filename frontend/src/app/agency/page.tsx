'use client'

import { useEffect, useState } from 'react'
import { auth, reconciliation, reports, integrations } from '@/lib/api'
import Link from 'next/link'

interface Summary {
  money_reconciled: number
  money_at_risk: number
  recoverable_amount: number
  issues_found: number
}

interface Discrepancy {
  id: string
  issue_type: string
  status: string
  amount: number
  customer_name: string
  date: string
  confidence_score: number
  suggested_cause: string
  ai_explanation: string | null
}

const ISSUE_LABELS: Record<string, string> = {
  missing_transaction: 'Missing Transaction',
  duplicate_transaction: 'Duplicate Entry',
  payout_mismatch: 'Payout Mismatch',
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


export default function AgencyWorkspace() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [discrepancies, setDiscrepancies] = useState<Discrepancy[]>([])
  const [runningRecon, setRunningRecon] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<'clients' | 'findings' | 'integrations'>('clients')
  const [uploadStatus, setUploadStatus] = useState<string>('')
  const [showImport, setShowImport] = useState(false)
  const [orgName, setOrgName] = useState('Sterling & Associates')


  const loadData = async () => {
    try {
      const [sumRes, listRes, meRes] = await Promise.all([
        reconciliation.summary(),
        reconciliation.list({ status: 'open', limit: 100 }),
        auth.me().catch(() => ({ data: { org_name: 'Sterling & Associates' } }))
      ])
      setSummary(sumRes.data)
      setDiscrepancies(listRes.data.items)
      if (meRes?.data?.org_name) {
        setOrgName(meRes.data.org_name)
      }
    } catch (e) {
      // Silently fail
    }
  }

  useEffect(() => { loadData() }, [])

  const runRecon = async () => {
    setRunningRecon(true)
    try {
      await reconciliation.run()
      await loadData()
    } catch (e) {
      console.error(e)
    }
    setRunningRecon(false)
  }



  const downloadReport = () => {
    const token = localStorage.getItem('rf_token')
    if (!token) return
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    window.open(`${API_BASE}/reports/view?token=${token}`, '_blank')
  }

  const handleCSVUpload = async (type: 'stripe' | 'quickbooks' | 'shopify', file: File) => {
    setUploadStatus(`Uploading ${type} data...`)
    try {
      const uploader = type === 'stripe' ? integrations.uploadStripeCSV : type === 'quickbooks' ? integrations.uploadQBCSV : integrations.uploadShopifyCSV
      const res = await uploader(file)
      setUploadStatus(`Imported ${res.data.imported} ${type} records`)
      setTimeout(() => setUploadStatus(''), 3000)
    } catch (e) {
      setUploadStatus(`Error uploading ${type} data`)
      setTimeout(() => setUploadStatus(''), 3000)
    }
  }

  const updateStatus = async (id: string, status: string) => {
    try {
      await reconciliation.updateStatus(id, status)
      await loadData()
    } catch (e) {
      console.error(e)
    }
  }

  const fmt = (n: number) => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

  // Compute revenue-focused metrics using database data
  const totalRevAtRisk = summary?.money_at_risk || 0
  const totalRecoverable = summary?.recoverable_amount || 0
  const totalFindings = summary?.issues_found || 0
  const totalCritical = summary?.issues_found || 0

  const clientsToShow = summary && summary.issues_found > 0 ? [
    {
      id: 'real-org',
      name: `${orgName} (Active Workspace)`,
      revenue_at_risk: summary.money_at_risk,
      recoverable_revenue: summary.recoverable_amount,
      open_findings: summary.issues_found,
      critical_findings: summary.issues_found,
      last_audit: 'Just now'
    }
  ] : []

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 bottom-0 w-64 bg-white border-r border-gray-200 z-40 flex flex-col">
        <div className="px-6 py-5 border-b">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center">
              <span className="text-white font-bold text-sm">R</span>
            </div>
            <span className="font-semibold text-lg text-gray-900">ReconFlow</span>
          </div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          <button
            onClick={() => setActiveView('clients')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${activeView === 'clients' ? 'bg-gray-100 text-gray-900' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
            Clients
          </button>
          <button
            onClick={() => setActiveView('findings')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${activeView === 'findings' ? 'bg-gray-100 text-gray-900' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
            Findings
          </button>
          <button
            onClick={() => setActiveView('integrations')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${activeView === 'integrations' ? 'bg-gray-100 text-gray-900' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 001 1h1a2 2 0 110 4h-1a1 1 0 00-1 1v3a1 1 0 01-1 1h-3a1 1 0 00-1 1v1a2 2 0 11-4 0v-1a1 1 0 00-1-1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" /></svg>
            Integrations
          </button>
        </nav>

        {/* Upload Section */}
        <div className="px-4 py-4 border-t">
          {!showImport ? (
            <button onClick={() => setShowImport(true)} className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-dashed border-gray-300 hover:border-gray-400 hover:bg-gray-50 transition text-sm text-gray-600 font-medium">
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
              Import Client Data
            </button>
          ) : (
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="text-xs font-semibold uppercase tracking-wider text-gray-500">Import Data</div>
                <button onClick={() => setShowImport(false)} className="text-gray-400 hover:text-gray-600">✕</button>
              </div>
              <div className="space-y-2">
                {(['stripe', 'quickbooks', 'shopify'] as const).map(type => (
                  <label key={type} className="flex items-center gap-2 px-3 py-2 rounded-lg border border-dashed border-gray-200 hover:border-gray-300 hover:bg-gray-50 cursor-pointer transition text-xs text-gray-600">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                    {type.charAt(0).toUpperCase() + type.slice(1)} CSV
                    <input type="file" accept=".csv" className="hidden" onChange={e => e.target.files?.[0] && handleCSVUpload(type, e.target.files[0])} />
                  </label>
                ))}
              </div>
              <div className="mt-3 p-3 bg-blue-50/50 rounded-lg border border-blue-100">
                <div className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <div className="text-[11px] text-blue-800 leading-tight">
                    <span className="font-semibold block mb-1">Standard Exports Only (Regular Plan)</span>
                    Please upload the default, out-of-the-box CSV exports directly from each platform. No manual column mapping or daily/monthly aggregate reports are supported.
                    <br/><br/>
                    Need custom CSV formats, P&amp;L parsing, or mapping? <a href="#" className="font-semibold underline hover:text-blue-900">Contact us for a Custom Plan</a>.
                  </div>
                </div>
              </div>
              {uploadStatus && <div className="text-xs text-emerald-600 mt-2 font-medium">{uploadStatus}</div>}
            </div>
          )}
        </div>

        <div className="px-4 py-3 border-t">

          <div className="flex gap-2">
            <button onClick={runRecon} disabled={runningRecon} className="flex-1 text-xs bg-emerald-600 text-white py-2 rounded-lg font-medium hover:bg-emerald-700 transition disabled:opacity-50">
              {runningRecon ? 'Running...' : 'Run Audit'}
            </button>
            <button onClick={downloadReport} className="text-xs bg-gray-100 text-gray-700 py-2 px-3 rounded-lg font-medium hover:bg-gray-200 transition" title="Download PDF">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="ml-64 p-8">
        {/* Status Toast */}
        {uploadStatus && (
          <div className="fixed top-4 right-4 z-50 bg-emerald-600 text-white text-sm font-medium px-5 py-3 rounded-xl shadow-lg shadow-emerald-600/20 flex items-center gap-2 animate-pulse">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            {uploadStatus}
          </div>
        )}

        {/* Summary Metrics — PHASE 3 */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="rf-metric-card rf-metric-card-risk">
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Revenue At Risk</div>
            <div className="text-3xl font-bold text-red-600 rf-number">${fmt(totalRevAtRisk)}</div>
          </div>
          <div className="rf-metric-card rf-metric-card-recover">
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Recoverable Revenue</div>
            <div className="text-3xl font-bold text-emerald-600 rf-number">${fmt(totalRecoverable)}</div>
          </div>
          <div className="rf-metric-card rf-metric-card-findings">
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Critical Findings</div>
            <div className="text-3xl font-bold text-gray-900 rf-number">{totalCritical}</div>
            <div className="text-xs text-gray-500 mt-1">{totalFindings} total</div>
          </div>
          <div className="rf-metric-card border-l-4 border-l-blue-500">
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Potential Client Value</div>
            <div className="text-3xl font-bold text-blue-600 rf-number">${fmt(totalRecoverable * 12)}</div>
            <div className="text-xs text-gray-500 mt-1">Annualized Recovery</div>
          </div>
        </div>

        {/* PHASE 6 — Client List (Agency Workspace) */}
        {activeView === 'clients' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">Client Risk Ranking</h2>
              <span className="text-sm text-gray-500">{clientsToShow.length} clients · Sorted by risk</span>
            </div>
            <div className="bg-white rounded-2xl border overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b">
                    <th className="text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider text-gray-500">Client Name</th>
                    <th className="text-right px-6 py-4 text-xs font-semibold uppercase tracking-wider text-gray-500">Revenue At Risk</th>
                    <th className="text-right px-6 py-4 text-xs font-semibold uppercase tracking-wider text-gray-500">Recoverable Revenue</th>
                    <th className="text-center px-6 py-4 text-xs font-semibold uppercase tracking-wider text-gray-500">Critical Findings</th>
                    <th className="text-center px-6 py-4 text-xs font-semibold uppercase tracking-wider text-gray-500">Priority</th>
                    <th className="text-right px-6 py-4 text-xs font-semibold uppercase tracking-wider text-gray-500"></th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {clientsToShow.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-16 text-center">
                        <div className="flex flex-col items-center justify-center">
                          <svg className="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                          <h3 className="text-lg font-medium text-gray-900 mb-1">No Client Data Yet</h3>
                          <p className="text-sm text-gray-500 max-w-sm mb-6">Connect your first client integration or upload CSV ledger files to start identifying revenue leakage.</p>
                          <button onClick={() => setShowImport(true)} className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white font-medium rounded-xl hover:bg-emerald-700 transition shadow-sm">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                            Import Data
                          </button>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    [...clientsToShow].sort((a, b) => b.revenue_at_risk - a.revenue_at_risk).map(client => (
                      <tr key={client.id} className="hover:bg-gray-50 transition">
                        <td className="px-6 py-4">
                          <div className="font-medium text-gray-900">{client.name}</div>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <span className="font-semibold text-red-600">${fmt(client.revenue_at_risk)}</span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <span className="font-semibold text-emerald-600">${fmt(client.recoverable_revenue)}</span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className="text-sm font-medium text-amber-600">{client.critical_findings}</span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          {(() => {
                            const score = client.revenue_at_risk * 0.6 + client.recoverable_revenue * 0.4;
                            let priority = 'Low';
                            let style = 'bg-gray-100 text-gray-700';
                            if (score > 15000) { priority = 'Critical'; style = 'bg-red-100 text-red-700'; }
                            else if (score > 8000) { priority = 'High'; style = 'bg-orange-100 text-orange-700'; }
                            else if (score > 3000) { priority = 'Medium'; style = 'bg-blue-100 text-blue-700'; }
                            return <span className={`text-xs font-bold uppercase px-2.5 py-1 rounded-full ${style}`}>{priority}</span>;
                          })()}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <Link
                            href={`/client-audit/${client.id}`}
                            className="text-sm font-medium text-blue-600 hover:text-blue-800 transition"
                          >
                            View Audit →
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Findings View */}
        {activeView === 'findings' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">Open Findings</h2>
            </div>
            {discrepancies.length > 0 ? (
              <div className="space-y-3">
                {discrepancies.map(d => {
                  const severity = (d.confidence_score || 0) >= 0.90 ? 'critical' : (d.confidence_score || 0) >= 0.80 ? 'warning' : 'info'
                  return (
                    <div key={d.id} className="rf-finding-block">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-3">
                          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full shrink-0 ${SEVERITY_STYLES[severity]}`}>
                            {severity}
                          </span>
                          <div>
                            <div className="font-semibold text-gray-900">{ISSUE_LABELS[d.issue_type] || d.issue_type}</div>
                            <div className="text-sm text-gray-500 mt-0.5">
                              {d.customer_name || 'Unknown'}{d.date ? ` · ${new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}` : ''}
                            </div>
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="text-lg font-bold text-red-600">${fmt(d.amount || 0)}</div>
                        </div>
                      </div>
                      {d.suggested_cause && (
                        <div className="mt-3 text-sm text-gray-600">{d.suggested_cause}</div>
                      )}
                      <div className="mt-3 flex gap-2">
                        <button onClick={() => updateStatus(d.id, 'resolved')} className="text-xs font-medium text-emerald-600 hover:text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded-lg transition">
                          ✓ Resolve
                        </button>
                        <button onClick={() => updateStatus(d.id, 'ignored')} className="text-xs font-medium text-gray-500 hover:text-gray-700 bg-gray-100 px-3 py-1.5 rounded-lg transition">
                          Dismiss
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="bg-white rounded-2xl border p-12 text-center">
                <div className="text-4xl mb-4">📊</div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">No findings yet</h3>
                <p className="text-sm text-gray-500 mb-6">Upload CSV data from Stripe, Shopify, or QuickBooks, then run an audit.</p>
                <button onClick={runRecon} className="text-sm bg-emerald-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-emerald-700 transition">
                  Run Audit
                </button>
              </div>
            )}
          </div>
        )}

        {/* Integrations View */}
        {activeView === 'integrations' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">Integrations</h2>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {[
                { name: 'Stripe Connect', logo: '💳', desc: 'Sync payments, payouts, and fees directly via Connect OAuth.', connectFn: async () => {
                  try {
                    const res = await integrations.stripeConnectUrl();
                    window.location.href = res.data.url;
                  } catch (e) {
                    alert('Error connecting Stripe. Make sure backend is running.');
                  }
                }},
                { name: 'QuickBooks Ledger', logo: '📊', desc: 'Match bank feeds and invoices by uploading financial exports.', mock: true },
                { name: 'Shopify Sales', logo: '🛍️', desc: 'Sync store orders and checkouts by uploading report exports.', mock: true }
              ].map((item, i) => (
                <div key={i} className="bg-white rounded-2xl border p-6 flex flex-col justify-between shadow-sm">
                  <div>
                    <div className="text-4xl mb-4">{item.logo}</div>
                    <h3 className="text-lg font-bold text-gray-900 mb-1">{item.name}</h3>
                    <p className="text-sm text-gray-500 leading-relaxed mb-6">{item.desc}</p>
                  </div>
                  {item.connectFn ? (
                    <button onClick={item.connectFn} className="w-full bg-blue-600 text-white font-medium py-2.5 rounded-xl text-sm hover:bg-blue-700 transition">
                      Connect Account
                    </button>
                  ) : (
                    <button onClick={() => alert(`${item.name} integration currently uses secure CSV file imports under 'Import Client Data' in the sidebar.`)} className="w-full bg-gray-100 text-gray-700 font-medium py-2.5 rounded-xl text-sm hover:bg-gray-200 transition">
                      CSV Import Ready
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
