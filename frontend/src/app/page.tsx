'use client'

import Link from 'next/link'


const HOW_IT_WORKS = [
  { step: '01', title: 'Find Lost Revenue', desc: 'Upload client financial data and uncover hidden revenue loss in minutes.' },
  { step: '02', title: 'Recover Missing Revenue', desc: 'Identify missing revenue, unpaid invoices, and financial risk before your client does.' },
  { step: '03', title: 'Prove Client Value', desc: 'Send a branded Revenue Risk Audit PDF directly to your client.' },
]

const USE_CASES = [
  { title: 'Monthly Client Reviews', desc: 'Automatically surface revenue discrepancies before your monthly client call. Show up with answers, not questions.' },
  { title: 'New Client Onboarding', desc: 'Run a free audit for prospects. Show them exactly how much money they are losing. Close the deal with data.' },
  { title: 'Upsell Advisory Services', desc: 'Use audit findings to justify higher-value advisory engagements. Turn bookkeeping into revenue recovery.' },
]

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center">
              <span className="text-white font-bold text-sm">R</span>
            </div>
            <span className="font-semibold text-lg text-gray-900 tracking-tight">ReconFlow</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-gray-600">
            <a href="#how-it-works" className="hover:text-gray-900 transition">How It Works</a>
            <a href="#use-cases" className="hover:text-gray-900 transition">Use Cases</a>
          </div>
          <div className="flex items-center gap-3">

            <Link href="/login" className="text-sm font-medium text-gray-700 hover:text-gray-900 transition px-3 py-2">
              Sign In
            </Link>
            <Link href="/signup" className="text-sm font-medium bg-emerald-600 text-white px-5 py-2.5 rounded-lg hover:bg-emerald-700 transition shadow-sm">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="rf-hero-gradient relative overflow-hidden pt-32 pb-24 md:pt-40 md:pb-32">
        <div className="rf-hero-glow rf-hero-glow-1" />
        <div className="rf-hero-glow rf-hero-glow-2" />
        <div className="max-w-6xl mx-auto px-6 relative z-10">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 bg-white/10 border border-white/10 rounded-full px-4 py-1.5 mb-6 rf-fade-up">
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              <span className="text-sm text-emerald-300 font-medium">Built for Accounting Agencies</span>
            </div>
            <h1 className="text-4xl md:text-6xl font-extrabold text-white leading-[1.1] tracking-tight mb-6 rf-fade-up rf-fade-up-delay-1">
              Find Revenue Your Clients Are Losing.
            </h1>
            <p className="text-lg md:text-xl text-gray-300 leading-relaxed max-w-2xl mb-10 rf-fade-up rf-fade-up-delay-2">
              Generate Revenue Risk Audits for Stripe, Shopify, and QuickBooks clients in minutes.
              Discover missing payments, financial findings, unpaid invoices, and recoverable revenue
              before your clients do.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 rf-fade-up rf-fade-up-delay-3">
              <Link
                href="/signup"
                className="inline-flex items-center justify-center gap-2 bg-emerald-500 text-white font-semibold px-8 py-4 rounded-xl text-lg hover:bg-emerald-400 transition shadow-lg shadow-emerald-500/25 rf-pulse"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                Get Started
              </Link>
              <a
                href="/sample-audit.pdf"
                download="Acme_Commerce_Revenue_Audit.pdf"
                className="inline-flex items-center justify-center gap-2 bg-white/10 text-white font-semibold px-8 py-4 rounded-xl text-lg border border-white/20 hover:bg-white/20 transition"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                Download Sample Audit
              </a>
              <a
                href="mailto:debansh@reconflow.com?subject=Book%20a%20Demo"
                className="inline-flex items-center justify-center gap-2 text-gray-300 font-semibold px-4 py-4 rounded-xl text-lg hover:text-white transition"
              >
                Book Demo
              </a>
            </div>
          </div>

          {/* Hero Stats */}
          <div className="grid grid-cols-3 gap-6 mt-16 max-w-xl rf-fade-up rf-fade-up-delay-4">
            {[
              { value: 'Zero', label: 'Manual Spreadsheets' },
              { value: 'Total', label: 'Revenue Visibility' },
              { value: 'Instant', label: 'Anomaly Detection' },
            ].map((s, i) => (
              <div key={i} className="text-center">
                <div className="text-2xl md:text-3xl font-bold text-white rf-number">{s.value}</div>
                <div className="text-xs md:text-sm text-gray-400 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>


      {/* Revenue at Risk Examples */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 tracking-tight mb-4">
              Revenue Slips Through the Cracks Every Day
            </h2>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              These are real categories of revenue loss found across e-commerce and SaaS businesses.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: '💸', title: 'Missing Transactions', desc: 'Payments received in Stripe but never recorded in QuickBooks. Revenue is understated and taxes may be wrong.' },
              { icon: '🔁', title: 'Unrecorded Refunds', desc: 'Refunds processed in Stripe but not reflected in your books. Revenue appears higher than it actually is.' },
              { icon: '🕳️', title: 'Revenue Leaks', desc: 'Shopify orders marked as paid but no matching payment collected. Money that should have been received was not.' },
            ].map((item, i) => (
              <div key={i} className="bg-gray-50 rounded-2xl p-8 border border-gray-100 hover:border-gray-200 hover:shadow-lg transition">
                <div className="text-3xl mb-4">{item.icon}</div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-sm text-gray-600 mb-4 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section id="how-it-works" className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 tracking-tight mb-4">
              How It Works
            </h2>
            <p className="text-lg text-gray-500">Three steps. Five minutes. Complete audit.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {HOW_IT_WORKS.map((s, i) => (
              <div key={i} className="relative bg-white rounded-2xl p-8 border border-gray-100">
                <div className="text-5xl font-black text-gray-100 mb-4">{s.step}</div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{s.title}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section id="use-cases" className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 tracking-tight mb-4">
              Built for Accounting Agencies
            </h2>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              ReconFlow helps you deliver more value to every client, every month.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {USE_CASES.map((uc, i) => (
              <div key={i} className="bg-slate-900 rounded-2xl p-8 text-white">
                <h3 className="text-lg font-bold mb-3">{uc.title}</h3>
                <p className="text-sm text-gray-300 leading-relaxed">{uc.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>


      {/* Final CTA */}
      <section className="py-20 bg-slate-900 text-white">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
            Stop Leaving Money on the Table
          </h2>
          <p className="text-lg text-gray-400 mb-10 max-w-xl mx-auto">
            Your clients are losing revenue right now. ReconFlow helps you find it, quantify it, and recover it.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/signup" className="inline-flex items-center justify-center gap-2 bg-emerald-500 text-white font-semibold px-8 py-4 rounded-xl text-lg hover:bg-emerald-400 transition shadow-lg shadow-emerald-500/25">
              Get Started
            </Link>
            <a href="mailto:debansh@reconflow.com?subject=Book%20a%20Demo" className="inline-flex items-center justify-center gap-2 bg-white/10 text-white font-semibold px-8 py-4 rounded-xl text-lg border border-white/20 hover:bg-white/20 transition">
              Book Demo
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-950 text-gray-500 py-12 border-t border-white/5">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-emerald-600 flex items-center justify-center">
              <span className="text-white text-xs font-bold">R</span>
            </div>
            <span className="text-sm font-medium text-gray-400">ReconFlow</span>
          </div>
          <div className="text-sm text-gray-600">Revenue Risk Audits for Accounting Agencies</div>
          <div className="text-sm">© 2024 ReconFlow. All rights reserved.</div>
        </div>
      </footer>
    </div>
  )
}
