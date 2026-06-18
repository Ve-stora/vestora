import axios from 'axios'
import { useAuthStore } from './authStore'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

// ── Auth ────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (email: string, password: string, full_name?: string) =>
    api.post('/api/auth/register', { email, password, full_name }),

  login: (email: string, password: string) =>
    api.post<{ access_token: string; token_type: string }>(
      '/api/auth/login',
      new URLSearchParams({ username: email, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
    ),
}

// ── Market ──────────────────────────────────────────────────────────────────
export const marketApi = {
  getStocks: () => api.get<StockSummary[]>('/api/market/stocks'),
  getStock: (symbol: string) => api.get<StockDetail>(`/api/market/stocks/${symbol}`),
  getForecast: (symbol: string) => api.get<Forecast>(`/api/market/forecast/${symbol}`),
}

// ── Portfolio ────────────────────────────────────────────────────────────────
export const portfolioApi = {
  get: () => api.get<Portfolio>('/api/portfolio'),
}

// ── AI ───────────────────────────────────────────────────────────────────────
export const aiApi = {
  query: (query: string, symbol?: string) =>
    api.post<{ query: string; response: string; disclaimer: string }>(
      '/api/ai/analytics',
      { query, symbol },
    ),
}

// ── Types ────────────────────────────────────────────────────────────────────
export interface StockSummary {
  symbol: string
  name: string
  sector: string | null
  exchange: string
  latest_price: number | null
  date: string | null
}

export interface StockDetail {
  symbol: string
  name: string
  sector: string | null
  exchange: string
  history: PriceBar[]
}

export interface PriceBar {
  date: string
  open: number | null
  high: number | null
  low: number | null
  close: number
  volume: number | null
}

export interface Forecast {
  symbol: string
  model: string
  horizon_days: number
  note: string
  forecast: { date: string; predicted_close: number; confidence: number }[]
}

export interface Holding {
  symbol: string
  shares: number
  avg_cost: number
  current_price: number
  market_value: number
  gain_loss: number
  gain_loss_pct: number
}

export interface Portfolio {
  holdings: Holding[]
  total_value: number
  total_cost: number
  total_gain_loss: number
}

export default api
