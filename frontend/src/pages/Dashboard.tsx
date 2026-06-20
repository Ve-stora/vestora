import { useStocks, useAnomalies } from '../hooks/useMarketData'

function StatCard({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent?: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-bold ${accent ?? 'text-white'}`}>{value}</p>
      {sub && <p className="text-gray-500 text-xs mt-1">{sub}</p>}
    </div>
  )
}

function TickerRow({ stock }: { stock: { symbol: string; name: string; close: number; change_pct: number | null; volume: number | null } }) {
  const chg  = stock.change_pct ?? 0
  const up   = chg >= 0
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-800 last:border-0">
      <div>
        <span className="text-white font-semibold text-sm">{stock.symbol}</span>
        <span className="text-gray-500 text-xs ml-2 hidden sm:inline">{stock.name}</span>
      </div>
      <div className="text-right">
        <span className="text-white text-sm font-mono">KES {stock.close.toFixed(2)}</span>
        <span className={`ml-3 text-xs font-semibold ${up ? 'text-emerald-400' : 'text-red-400'}`}>
          {up ? '+' : ''}{chg.toFixed(2)}%
        </span>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { stocks, loading: stocksLoading }       = useStocks('NSE')
  const { anomalies, loading: anomaliesLoading } = useAnomalies('NSE', 7)

  const gainers = [...stocks].sort((a, b) => (b.change_pct ?? 0) - (a.change_pct ?? 0)).slice(0, 5)
  const losers  = [...stocks].sort((a, b) => (a.change_pct ?? 0) - (b.change_pct ?? 0)).slice(0, 5)

  const avgChange = stocks.length
    ? stocks.reduce((s, x) => s + (x.change_pct ?? 0), 0) / stocks.length
    : 0

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white">NSE Market Overview</h1>
        <p className="text-gray-400 text-sm mt-0.5">End-of-day data · Nairobi Securities Exchange</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Listed Securities" value={stocks.length ? `${stocks.length}` : '—'} sub="NSE equities" />
        <StatCard
          label="Market Avg Change"
          value={stocksLoading ? '…' : `${avgChange >= 0 ? '+' : ''}${avgChange.toFixed(2)}%`}
          accent={avgChange >= 0 ? 'text-emerald-400' : 'text-red-400'}
          sub="vs. previous close"
        />
        <StatCard
          label="Anomalies Detected"
          value={anomaliesLoading ? '…' : `${anomalies.length}`}
          sub="last 7 days"
          accent={anomalies.length > 0 ? 'text-amber-400' : 'text-white'}
        />
        <StatCard label="Exchange" value="NSE" sub="Nairobi · EAT UTC+3" />
      </div>

      {/* Movers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Top Gainers</h2>
          {stocksLoading
            ? <p className="text-gray-500 text-sm">Loading…</p>
            : gainers.map((s) => <TickerRow key={s.symbol} stock={s} />)
          }
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Top Losers</h2>
          {stocksLoading
            ? <p className="text-gray-500 text-sm">Loading…</p>
            : losers.map((s) => <TickerRow key={s.symbol} stock={s} />)
          }
        </div>
      </div>

      {/* Anomaly flags */}
      {anomalies.length > 0 && (
        <div className="bg-amber-900/20 border border-amber-700/40 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-amber-400 uppercase tracking-wider mb-3">
            Statistical Anomalies — Last 7 Days
          </h2>
          <div className="space-y-2">
            {anomalies.slice(0, 5).map((a, i) => (
              <div key={i} className="flex items-start gap-3 text-sm">
                <span className="text-amber-500 font-semibold mt-0.5">{a.symbol}</span>
                <span className="text-gray-400">{a.description}</span>
                <span className="ml-auto text-gray-600 text-xs whitespace-nowrap">{a.date}</span>
              </div>
            ))}
          </div>
          <p className="text-gray-600 text-xs mt-3 italic">
            Statistical outliers only — not investment advice.
          </p>
        </div>
      )}
    </div>
  )
}