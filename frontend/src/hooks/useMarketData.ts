import { useState, useEffect, useCallback, useRef } from 'react'
import { marketApi, StockSummary, StockDetail, Forecast } from '../lib/api'

// ── Stock list ────────────────────────────────────────────────────────────────

export function useMarketData() {
  const [stocks, setStocks] = useState<StockSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStocks = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await marketApi.getStocks()
      setStocks(data)
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
      .then(({ data }) => {
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
      .then(({ data }) => {
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