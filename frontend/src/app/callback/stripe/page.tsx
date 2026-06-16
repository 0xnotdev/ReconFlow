'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import axios from 'axios'

export default function StripeCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState('Verifying Stripe connection...')
  const [error, setError] = useState('')

  useEffect(() => {
    const code = searchParams.get('code')
    if (!code) {
      setError('No authorization code received.')
      return
    }

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const token = localStorage.getItem('rf_token')

    axios.post(
      `${API_BASE}/stripe/callback`,
      { code },
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then(() => {
        setStatus('Successfully connected! Importing transactions...')
        setTimeout(() => {
          router.push('/agency')
        }, 2000)
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Failed to complete connection. Please try again.')
      })
  }, [searchParams, router])

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center text-white p-6 relative">
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      
      <div className="max-w-md w-full text-center space-y-6 relative z-10">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center shadow-lg shadow-emerald-500/20 mx-auto">
          <span className="text-white font-bold text-2xl">R</span>
        </div>

        {error ? (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-red-500">Connection Failed</h2>
            <p className="text-gray-400 text-sm">{error}</p>
            <button
              onClick={() => router.push('/agency')}
              className="inline-flex justify-center bg-white/10 text-white border border-white/10 px-5 py-2.5 rounded-xl hover:bg-white/20 transition font-semibold text-sm"
            >
              Back to Dashboard
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <h2 className="text-xl font-semibold text-gray-200">{status}</h2>
          </div>
        )}
      </div>
    </div>
  )
}
