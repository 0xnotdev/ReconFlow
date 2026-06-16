import React from 'react';

export function SampleAudit() {
  return (
    <div className="rf-audit-preview max-w-4xl mx-auto border border-gray-200 rounded-xl overflow-hidden shadow-xl bg-white">
      {/* Audit Header */}
      <div className="bg-slate-900 text-white px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold tracking-widest text-emerald-400 uppercase mb-1">Revenue Risk Audit</div>
            <div className="text-xl font-bold">Acme Commerce Co.</div>
            <div className="text-sm text-gray-400">January 1 – March 31, 2024</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-400 uppercase tracking-wider">Revenue At Risk</div>
            <div className="text-3xl font-bold text-red-400">$23,421</div>
          </div>
        </div>
      </div>

      {/* Audit Metrics */}
      <div className="grid grid-cols-4 divide-x border-b">
        {[
          { label: 'Revenue At Risk', value: '$23,421', color: 'text-red-600' },
          { label: 'Recoverable Revenue', value: '$14,112', color: 'text-emerald-600' },
          { label: 'Critical Findings', value: '9', color: 'text-amber-600' },
          { label: 'Recommended Actions', value: '25', color: 'text-blue-600' },
        ].map((m, i) => (
          <div key={i} className="px-6 py-5 text-center">
            <div className="text-xs text-gray-500 uppercase tracking-wider font-medium">{m.label}</div>
            <div className={`text-2xl font-bold mt-1 ${m.color}`}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* Audit Findings */}
      <div className="px-8 py-6">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Top Findings</div>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-100">
            <div className="flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-red-500"></span>
              <div>
                <div className="text-sm font-semibold text-gray-900">Missing Transaction</div>
                <div className="text-xs text-gray-500">Sarah Mitchell · Feb 14, 2024</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-bold text-red-600">$2,400.00</div>
              <div className="text-xs text-emerald-600 font-medium">Recoverable</div>
            </div>
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-100">
            <div className="flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-red-500"></span>
              <div>
                <div className="text-sm font-semibold text-gray-900">Refund Not Recorded</div>
                <div className="text-xs text-gray-500">Elena Rodriguez · Mar 5, 2024</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-bold text-red-600">$3,200.00</div>
              <div className="text-xs text-red-500 font-medium">At Risk</div>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t flex justify-between items-center">
          <div className="text-sm text-gray-500">Showing 2 of 25 findings.</div>
          <a href="/demo" className="text-sm font-semibold text-emerald-600 hover:text-emerald-700">View Full Sample Audit &rarr;</a>
        </div>
      </div>
    </div>
  )
}
