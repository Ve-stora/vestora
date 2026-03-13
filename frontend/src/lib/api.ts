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
    api
      .post<RegisterResponse>('/api/auth/register', { email, password, full_name })
      .then((r) => r.data),

  login: (email: string, password: string) =>
    api
      .post<{ access_token: string; token_type: string }>(
        '/api/auth/login',
        new URLSearchParams({ username: email, password }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
      )
      .then((r) => r.data),

  me: () => api.get<RegisterResponse>('/api/auth/me').then((r) => r.data),
}

// ── Market ──────────────────────────────────────────────────────────────────
export const marketApi = {
  // Defensive fallbacks (`?? []`) below: if the backend ever returns a
  // payload without the expected key (empty DB, partial outage, schema
  // drift) we get an empty list instead of `undefined` blowing up every
  // `.map`/`.sort`/spread call downstream in the hooks and pages.
  getStocks: () =>
    api
      .get<{ total: number; stocks: StockSummary[] }>('/api/market/stocks')
      .then((r) => r.data.stocks ?? []),

  getStock: (symbol: string) =>
    api.get<StockDetail>(`/api/market/stocks/${symbol}`).then((r) => r.data),

  getForecast: (symbol: string, horizon: 5 | 20 = 5) =>
    api.get<Forecast>(`/api/market/forecast/${symbol}`, { params: { horizon } }).then((r) => r.data),

  getAnomalies: (symbol: string, days = 7) =>
    api
      .get<{ anomalies: AnomalyFlag[] }>(`/api/market/anomalies/${symbol}`, { params: { days } })
      .then((r) => r.data.anomalies ?? []),

  getIndices: () =>
    api
      .get<{ indices: MarketIndexData[] }>('/api/market/indices')
      .then((r) => r.data.indices ?? []),

  getMovers: (limit = 10) =>
    api
      .get<MoversResponse>('/api/market/movers', { params: { limit } })
      .then((r) => r.data),
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
  last_price: number | null
  price_change: number | null
  price_change_pct: number | null
  last_synced: string | null
}

export interface StockDetail {
  symbol: string
  name: string
  sector: string | null
  last_price: number | null
  price_change: number | null
  price_change_pct: number | null
  history: PriceBar[]
  last_synced: string | null
}

export interface PriceBar {
  date: string
  close: number
  volume: number | null
}

export interface Forecast {
  symbol: string
  forecast_horizon: number
  predictions: number[]
  confidence_lower: number[]
  confidence_upper: number[]
  forecast_dates: string[]
  mape: number
  signal: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  signal_strength: number
  generated_at: string
  disclaimer: string
}

export interface AnomalyFlag {
  symbol: string
  date: string
  is_anomaly: boolean
  anomaly_score: number
  anomaly_type: string[]
  severity: 'LOW' | 'MEDIUM' | 'HIGH'
  description: string
  price: number
  volume: number
  price_change_pct: number
}

export interface MarketIndexData {
  name: string
  value: number
  change: number | null
  recorded_at: string | null
}

export interface MoverStock {
  symbol: string
  name: string
  sector: string | null
  last_price: number | null
  price_change: number | null
  price_change_pct: number
}

export interface MoversResponse {
  as_of: string
  gainers: MoverStock[]
  losers: MoverStock[]
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

export interface RegisterResponse {
  id: string
  email: string
  full_name: string | null
  tier: 'free' | 'premium' | 'b2b'
}

export default api