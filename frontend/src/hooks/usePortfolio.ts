import { useState, useEffect, useCallback } from 'react'
import { portfolioApi, Portfolio, Holding } from '../lib/api'

export function usePortfolio() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPortfolio = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await portfolioApi.get()
      setPortfolio(data)
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Failed to load portfolio.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchPortfolio()
  }, [fetchPortfolio])

  // Derived metrics
  const metrics = portfolio
    ? {
        totalValue: portfolio.total_value,
        totalCost: portfolio.total_cost,
        totalGainLoss: portfolio.total_gain_loss,
        totalGainLossPct:
          portfolio.total_cost > 0
            ? (portfolio.total_gain_loss / portfolio.total_cost) * 100
            : 0,
        holdingCount: portfolio.holdings.length,
        topGainer: [...(portfolio.holdings ?? [])].sort(
          (a, b) => b.gain_loss_pct - a.gain_loss_pct,
        )[0] as Holding | undefined,
        topLoser: [...(portfolio.holdings ?? [])].sort(
          (a, b) => a.gain_loss_pct - b.gain_loss_pct,
        )[0] as Holding | undefined,
      }
    : null

  return { portfolio, metrics, loading, error, refetch: fetchPortfolio }
}