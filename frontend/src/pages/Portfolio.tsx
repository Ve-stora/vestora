import { Link } from 'react-router-dom'
import { usePortfolio } from '../hooks/usePortfolio'
import type { Holding } from '../lib/api'

function fmt(n: number, decimals = 2) {
  return n.toLocaleString('en-KE', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

function PnlBadge({ pct }: { pct: number }) {
  const positive = pct >= 0
  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded ${
        positive
          ? 'bg-emerald-500/10 text-emerald-400'
          : 'bg-red-500/10 text-red-400'
      }`}
    >
      {positive ? '▲' : '▼'} {Math.abs(pct).toFixed(2)}%
    </span>
  )
}

function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string
  value: string
  sub?: string
  accent?: 'green' | 'red' | 'neutral'
}) {
  const colors: Record<string, string> = {
    green: 'text-emerald-400',
    red: 'text-red-400',
    neutral: 'text-white',
  }
  return (
    <div className="bg-zinc-900/70 border border-zinc-800 rounded-xl p-5">
      <p className="text-zinc-500 text-xs uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-bold font-mono ${colors[accent ?? 'neutral']}`}>
        {value}
      </p>
      {sub && <p className="text-zinc-600 text-xs mt-1">{sub}</p>}
    </div>
  )
}

export default function Portfolio() {
  const { portfolio, metrics, loading, error, refetch } = usePortfolio()

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 animate-pulse">
              <div className="h-3 bg-zinc-800 rounded w-1/2 mb-3" />
              <div className="h-7 bg-zinc-800 rounded w-3/4" />
            </div>
          ))}
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl h-64 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
          <p className="text-red-400 mb-3">{error}</p>
          <button
            onClick={refetch}
            className="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm px-4 py-2 rounded-lg transition"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const holdings: Holding[] = portfolio?.holdings ?? []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-white text-2xl font-bold">Portfolio</h1>
          <p className="text-zinc-500 text-sm mt-0.5">Your East African equity positions</p>
        </div>
        <button
          onClick={refetch}
          className="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm px-4 py-2 rounded-lg transition flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h5M20 20v-5h-5M4 9a9 9 0 0114.83-4.83M20 15a9 9 0 01-14.83 4.83" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard
            label="Total Value"
            value={`KES ${fmt(metrics.totalValue)}`}
            sub={`${metrics.holdingCount} position${metrics.holdingCount !== 1 ? 's' : ''}`}
          />
          <StatCard
            label="Total Cost"
            value={`KES ${fmt(metrics.totalCost)}`}
          />
          <StatCard
            label="Unrealised P&L"
            value={`${metrics.totalGainLoss >= 0 ? '+' : ''}KES ${fmt(metrics.totalGainLoss)}`}
            sub={`${metrics.totalGainLossPct >= 0 ? '+' : ''}${fmt(metrics.totalGainLossPct)}%`}
            accent={metrics.totalGainLoss >= 0 ? 'green' : 'red'}
          />
          <StatCard
            label="Top Gainer"
            value={metrics.topGainer?.symbol ?? '—'}
            sub={
              metrics.topGainer
                ? `+${fmt(metrics.topGainer.gain_loss_pct)}%`
                : undefined
            }
            accent="green"
          />
        </div>
      )}

      {/* Holdings Table */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-zinc-800">
          <h2 className="text-white font-semibold text-sm">Holdings</h2>
        </div>

        {holdings.length === 0 ? (
          <div className="text-center py-20 text-zinc-600">
            <svg className="w-12 h-12 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p>No holdings yet. Explore the <Link to="/market" className="text-emerald-400 hover:underline">Market</Link>.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-zinc-500 text-xs uppercase tracking-wider border-b border-zinc-800">
                <th className="text-left px-5 py-3">Symbol</th>
                <th className="text-right px-5 py-3 hidden sm:table-cell">Shares</th>
                <th className="text-right px-5 py-3 hidden md:table-cell">Avg Cost</th>
                <th className="text-right px-5 py-3">Price</th>
                <th className="text-right px-5 py-3">Market Value</th>
                <th className="text-right px-5 py-3">P&L</th>
                <th className="text-right px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {holdings.map((h: Holding) => (
                <tr key={h.symbol} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition">
                  <td className="px-5 py-3">
                    <span className="font-mono text-emerald-400 font-semibold">{h.symbol}</span>
                  </td>
                  <td className="px-5 py-3 text-right text-zinc-300 font-mono hidden sm:table-cell">
                    {h.shares.toLocaleString()}
                  </td>
                  <td className="px-5 py-3 text-right text-zinc-400 font-mono hidden md:table-cell">
                    {fmt(h.avg_cost)}
                  </td>
                  <td className="px-5 py-3 text-right text-white font-mono">
                    {fmt(h.current_price)}
                  </td>
                  <td className="px-5 py-3 text-right text-white font-mono">
                    {fmt(h.market_value)}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <div className="flex flex-col items-end gap-0.5">
                      <span className={`font-mono text-xs ${h.gain_loss >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {h.gain_loss >= 0 ? '+' : ''}{fmt(h.gain_loss)}
                      </span>
                      <PnlBadge pct={h.gain_loss_pct} />
                    </div>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <Link
                      to={`/stocks/${h.symbol}`}
                      className="text-xs text-emerald-400 hover:text-emerald-300 transition"
                    >
                      →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div className="px-5 py-3 border-t border-zinc-800">
          <p className="text-zinc-700 text-xs">
            Prices update every 30 s. Values are indicative only and do not constitute financial advice.
          </p>
        </div>
      </div>
    </div>
  )
}