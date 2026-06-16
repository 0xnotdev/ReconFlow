import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: API_BASE })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('rf_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const auth = {
  register: (data: any) => api.post('/auth/register', data),
  login: (email: string, password: string) =>
    api.post('/auth/token', new URLSearchParams({ username: email, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    ),
  me: () => api.get('/auth/me'),
}

export const clients = {
  list: () => api.get('/clients/'),
  create: (name: string) => api.post('/clients/', { name }),
  delete: (id: string) => api.delete(`/clients/${id}`),
}

export const reconciliation = {
  run: (client_id?: string) => api.post('/reconciliation/run', { client_id: client_id || null }),
  summary: (client_id?: string) => api.get('/discrepancies/summary', { params: { client_id } }),
  list: (params?: any) => api.get('/discrepancies/', { params }),
  updateStatus: (id: string, status: string) =>
    api.patch(`/discrepancies/${id}/status`, { status }),
  explain: (id: string) => api.get(`/discrepancies/${id}/explain`),
  loadSampleData: () => api.post('/demo/load-sample-data'),
}

export const integrations = {
  stripeConnectUrl: () => api.get('/stripe/connect-url'),
  uploadStripeCSV: (file: File, clientId: string) => {
    const form = new FormData(); form.append('file', file); form.append('client_id', clientId);
    return api.post('/stripe/upload-csv', form)
  },
  uploadQBCSV: (file: File, clientId: string) => {
    const form = new FormData(); form.append('file', file); form.append('client_id', clientId);
    return api.post('/quickbooks/upload-csv', form)
  },
  uploadShopifyCSV: (file: File, clientId: string) => {
    const form = new FormData(); form.append('file', file); form.append('client_id', clientId);
    return api.post('/shopify/upload-csv', form)
  },
}

export const reports = {
  download: () => api.get('/reports/download', { responseType: 'blob' }),
}
