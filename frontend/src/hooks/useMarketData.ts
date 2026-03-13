import { useState, useEffect, useCallback, useRef } from 'react'
import {
  marketApi,
  StockSummary,
  StockDetail,
  Forecast,
  AnomalyFlag,
  MarketIndexData,
  MoverStock,
} from '../lib/api'

// ── Stock list ────────────────────────────────────────────────────────────────

export function useMarketData() {
  const [stocks, setStocks] = useState<StockSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStocks = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await marketApi.getStocks()
      setStocks(data ?? [])
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Failed to load market data.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStocks()
  }, [fetchStocks])

  return { stocks, loading, error, refetch: fetchStocks }
}

/**
 * Flat "TickerRow"-shaped stock list. Named/shaped this way (with `exchange`
 * accepted but unused) because the live backend is NSE-only for now — this
 * keeps the call site stable for when USE/DSE/RSE support lands.
 */
export function useStocks(_exchange: string = 'NSE') {
  const { stocks: raw, loading, error, refetch } = useMarketData()
  const stocks = raw.map((s) => ({
    symbol: s.symbol,
    name: s.name,
    close: s.last_price ?? 0,
    change_pct: s.price_change_pct,
    volume: null as number | null,
  }))
  return { stocks, loading, error, refetch }
}

// ── Single stock ──────────────────────────────────────────────────────────────

export function useStockDetail(symbol: string | undefined) {
  const [stock, setStock] = useState<StockDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!symbol) return
    let cancelled = false
    setLoading(true)
    setError(null)
    marketApi
      .getStock(symbol)
      .then((data) => {
        if (!cancelled) setStock(data)
      })
      .catch((err) => {
        if (!cancelled)
          setError(err?.response?.data?.detail ?? 'Failed to load stock.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [symbol])

  return { stock, loading, error }
}

// ── Forecast ──────────────────────────────────────────────────────────────────

export function useForecast(symbol: string | undefined) {
  const [forecast, setForecast] = useState<Forecast | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!symbol) return
    let cancelled = false
    setLoading(true)
    setError(null)
    marketApi
      .getForecast(symbol)
      .then((data) => {
        if (!cancelled) setForecast(data)
      })
      .catch((err) => {
        if (!cancelled)
          setError(err?.response?.data?.detail ?? 'Forecast unavailable.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [symbol])

  return { forecast, loading, error }
}

// ── Anomalies (exchange-wide, fanned out client-side) ─────────────────────────
// The live backend only exposes anomaly detection per-symbol
// (GET /api/market/anomalies/{symbol}), not an exchange-wide feed. This fans
// out across the current stock list — fine at ~20 NSE symbols, but a real
// aggregate endpoint would be the better fix once the universe grows.

export function useAnomalies(_exchange: string = 'NSE', days = 7) {
  const { stocks } = useMarketData()
  const [anomalies, setAnomalies] = useState<AnomalyFlag[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (stocks.length === 0) return
    let cancelled = false
    setLoading(true)

    Promise.allSettled(stocks.map((s) => marketApi.getAnomalies(s.symbol, days)))
      .then((results) => {
        if (cancelled) return
        const flagged = results
          .filter((r): r is PromiseFulfilledResult<AnomalyFlag[]> => r.status === 'fulfilled')
          .flatMap((r) => r.value)
          .filter((a) => a.is_anomaly)
        setAnomalies(flagged)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [stocks.length, days])

  return { anomalies, loading }
}

// ── Market indices (NSE 20, NASI) ──────────────────────────────────────────────

export function useIndices() {
  const [indices, setIndices] = useState<MarketIndexData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchIndices = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await marketApi.getIndices()
      setIndices(data ?? [])
    } catch {
      // Indices are a nice-to-have header strip — fail quietly rather than
      // blocking the rest of the dashboard from rendering.
      setError('Index data unavailable.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchIndices()
  }, [fetchIndices])

  return { indices, loading, error, refetch: fetchIndices }
}

// ── Server-computed top movers ─────────────────────────────────────────────────

export function useMarketMovers(limit = 5) {
  const [gainers, setGainers] = useState<MoverStock[]>([])
  const [losers, setLosers] = useState<MoverStock[]>([])
  const [asOf, setAsOf] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchMovers = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await marketApi.getMovers(limit)
      setGainers(data.gainers ?? [])
      setLosers(data.losers ?? [])
      setAsOf(data.as_of ?? null)
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Failed to load market movers.')
    } finally {
      setLoading(false)
    }
  }, [limit])

  useEffect(() => {
    fetchMovers()
  }, [fetchMovers])

  return { gainers, losers, asOf, loading, error, refetch: fetchMovers }
}

// ── Auto-refresh ──────────────────────────────────────────────────────────────

export function usePolledMarketData(intervalMs = 30_000) {
  const { stocks, loading, error, refetch } = useMarketData()
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    intervalRef.current = setInterval(refetch, intervalMs)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [refetch, intervalMs])

  return { stocks, loading, error, refetch }
}