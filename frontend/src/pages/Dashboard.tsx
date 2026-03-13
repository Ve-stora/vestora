import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from 'recharts'
import { useStocks, useAnomalies, useIndices, useMarketMovers } from '../hooks/useMarketData'
import type { MoverStock } from '../lib/api'

function StatCard({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent?: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-bold ${accent ?? 'text-white'}`}>{value}</p>
      {sub && <p className="text-gray-500 text-xs mt-1">{sub}</p>}
    </div>
  )
}

function IndexBadge({ name, value, change, loading }: { name: string; value?: number; change?: number | null; loading?: boolean }) {
  const up = (change ?? 0) >= 0
  return (
    <div className="flex items-center gap-3 bg-gray-900 border border-gray-800 rounded-lg px-4 py-2.5 shrink-0">
      <span className="text-gray-300 text-sm font-semibold whitespace-nowrap">{name}</span>
      {loading ? (
        <span className="text-gray-600 text-sm">…</span>
      ) : value === undefined ? (
        <span className="text-gray-600 text-sm">—</span>
      ) : (
        <>
          <span className="text-white text-sm font-mono">{value.toLocaleString('en-KE', { maximumFractionDigits: 2 })}</span>
          {change != null && (
            <span className={`text-xs font-semibold ${up ? 'text-emerald-400' : 'text-red-400'}`}>
              {up ? '+' : ''}{change.toFixed(2)}
            </span>
          )}
        </>
      )}
    </div>
  )
}

function TickerRow({ stock }: { stock: { symbol: string; name: string; close: number; change_pct: number | null; volume: number | null } }) {
  const chg = stock.change_pct ?? 0
  const up = chg >= 0
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

function moverToStock(m: MoverStock) {
  return {
    symbol: m.symbol,
    name: m.name,
    close: m.last_price ?? 0,
    change_pct: m.price_change_pct,
    volume: null as number | null,
  }
}

function EmptyState({ message }: { message: string }) {
  return <p className="text-gray-600 text-sm py-6 text-center">{message}</p>
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="bg-red-900/20 border border-red-700/40 rounded-lg px-4 py-3 text-red-400 text-sm">
      {message}
    </div>
  )
}

export default function Dashboard() {
  const { stocks, loading: stocksLoading, error: stocksError, refetch: refetchStocks } = useStocks('NSE')
  const { anomalies, loading: anomaliesLoading } = useAnomalies('NSE', 7)
  const { indices, loading: indicesLoading } = useIndices()
  const {
    gainers,
    losers,
    loading: moversLoading,
    error: moversError,
  } = useMarketMovers(5)

  const avgChange = stocks.length
    ? stocks.reduce((s, x) => s + (x.change_pct ?? 0), 0) / stocks.length
    : 0

  // Chart data: top gainers + top losers, sorted so the bar chart reads
  // left-to-right from biggest loser to biggest gainer.
  const chartData = [...losers, ...gainers]
    .filter((m) => m.price_change_pct != null)
    .sort((a, b) => a.price_change_pct - b.price_change_pct)
    .map((m) => ({ symbol: m.symbol, change: m.price_change_pct }))

  const nasi = indices.find((i) => i.name.toUpperCase().includes('NASI'))
  const nse20 = indices.find((i) => i.name.toUpperCase().includes('NSE 20') || i.name.toUpperCase().includes('NSE20'))

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">NSE Market Overview</h1>
          <p className="text-gray-400 text-sm mt-0.5">End-of-day data · Nairobi Securities Exchange</p>
        </div>
        <button
          onClick={refetchStocks}
          disabled={stocksLoading}
          className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-300 text-sm px-4 py-2 rounded-lg transition"
        >
          <svg className={`w-4 h-4 ${stocksLoading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h5M20 20v-5h-5M4 9a9 9 0 0114.83-4.83M20 15a9 9 0 01-14.83 4.83" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Index strip */}
      <div className="flex gap-3 overflow-x-auto pb-1">
        <IndexBadge name="NASI" value={nasi?.value} change={nasi?.change} loading={indicesLoading} />
        <IndexBadge name="NSE 20" value={nse20?.value} change={nse20?.change} loading={indicesLoading} />
      </div>

      {stocksError && <ErrorBanner message={stocksError} />}

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Listed Securities" value={stocksLoading ? '…' : stocks.length ? `${stocks.length}` : '—'} sub="NSE equities" />
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

      {/* Movers chart */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Top Movers — % Change</h2>
        {moversError ? (
          <ErrorBanner message={moversError} />
        ) : moversLoading ? (
          <p className="text-gray-500 text-sm">Loading…</p>
        ) : chartData.length === 0 ? (
          <EmptyState message="No mover data available yet." />
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                <XAxis dataKey="symbol" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={{ stroke: '#27272a' }} tickLine={false} />
                <YAxis
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  axisLine={{ stroke: '#27272a' }}
                  tickLine={false}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', borderRadius: 8 }}
                  labelStyle={{ color: '#e5e7eb' }}
                  formatter={(value: number) => [`${value.toFixed(2)}%`, 'Change']}
                />
                <Bar dataKey="change" radius={[4, 4, 0, 0]}>
                  {chartData.map((d, i) => (
                    <Cell key={i} fill={d.change >= 0 ? '#34d399' : '#f87171'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Movers lists */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Top Gainers</h2>
          {moversError ? (
            <ErrorBanner message={moversError} />
          ) : moversLoading ? (
            <p className="text-gray-500 text-sm">Loading…</p>
          ) : gainers.length === 0 ? (
            <EmptyState message="No gainers to show." />
          ) : (
            gainers.map((s) => <TickerRow key={s.symbol} stock={moverToStock(s)} />)
          )}
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Top Losers</h2>
          {moversError ? (
            <ErrorBanner message={moversError} />
          ) : moversLoading ? (
            <p className="text-gray-500 text-sm">Loading…</p>
          ) : losers.length === 0 ? (
            <EmptyState message="No losers to show." />
          ) : (
            losers.map((s) => <TickerRow key={s.symbol} stock={moverToStock(s)} />)
          )}
        </div>
      </div>

      {/* Anomaly flags */}
      <div className="bg-amber-900/20 border border-amber-700/40 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-amber-400 uppercase tracking-wider mb-3">
          Statistical Anomalies — Last 7 Days
        </h2>
        {anomaliesLoading ? (
          <p className="text-gray-500 text-sm">Scanning…</p>
        ) : anomalies.length === 0 ? (
          <EmptyState message="No statistical anomalies flagged in the last 7 days." />
        ) : (
          <div className="space-y-2">
            {anomalies.slice(0, 5).map((a, i) => (
              <div key={i} className="flex items-start gap-3 text-sm">
                <span className="text-amber-500 font-semibold mt-0.5">{a.symbol}</span>
                <span className="text-gray-400">{a.description}</span>
                <span className="ml-auto text-gray-600 text-xs whitespace-nowrap">{a.date}</span>
              </div>
            ))}
          </div>
        )}
        <p className="text-gray-600 text-xs mt-3 italic">
          Statistical outliers only — not investment advice.
        </p>
      </div>
    </div>
  )
}