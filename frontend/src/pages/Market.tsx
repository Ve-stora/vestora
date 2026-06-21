import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { usePolledMarketData } from '../hooks/useMarketData'
import type { StockSummary } from '../lib/api'

type SortKey = 'symbol' | 'name' | 'latest_price' | 'exchange'
type SortDir = 'asc' | 'desc'

const EXCHANGES = ['ALL', 'NSE', 'USE', 'DSE', 'RSE'] as const

export default function Market() {
  const { stocks, loading, error, refetch } = usePolledMarketData(30_000)
  const [search, setSearch] = useState('')
  const [exchange, setExchange] = useState<string>('ALL')
  const [sortKey, setSortKey] = useState<SortKey>('symbol')
  const [sortDir, setSortDir] = useState<SortDir>('asc')

  const filtered = useMemo(() => {
    let list = stocks
    if (exchange !== 'ALL') list = list.filter((s) => s.exchange === exchange)
    if (search.trim()) {
      const q = search.trim().toLowerCase()
      list = list.filter(
        (s) =>
          s.symbol.toLowerCase().includes(q) ||
          s.name.toLowerCase().includes(q) ||
          (s.sector ?? '').toLowerCase().includes(q),
      )
    }
    return [...list].sort((a, b) => {
      const av = a[sortKey] ?? ''
      const bv = b[sortKey] ?? ''
      const cmp = av < bv ? -1 : av > bv ? 1 : 0
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [stocks, exchange, search, sortKey, sortDir])

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const SortIcon = ({ k }: { k: SortKey }) => (
    <span className="ml-1 text-zinc-600">
      {sortKey === k ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}
    </span>
  )

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-white text-2xl font-bold">Market</h1>
          <p className="text-zinc-500 text-sm mt-0.5">NSE · USE · DSE · RSE</p>
        </div>
        <button
          onClick={refetch}
          disabled={loading}
          className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-zinc-300 text-sm px-4 py-2 rounded-lg transition"
        >
          <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h5M20 20v-5h-5M4 9a9 9 0 0114.83-4.83M20 15a9 9 0 01-14.83 4.83" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-5">
        <input
          type="text"
          placeholder="Search symbol, name, or sector…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2 text-white placeholder-zinc-600 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/30 transition"
        />
        <div className="flex gap-1">
          {EXCHANGES.map((ex) => (
            <button
              key={ex}
              onClick={() => setExchange(ex)}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition ${
                exchange === ex
                  ? 'bg-emerald-500 text-black'
                  : 'bg-zinc-900 border border-zinc-800 text-zinc-400 hover:border-zinc-600'
              }`}
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 text-zinc-400 text-xs uppercase tracking-wider">
              <th
                className="text-left px-4 py-3 cursor-pointer hover:text-zinc-200 select-none"
                onClick={() => toggleSort('symbol')}
              >
                Symbol <SortIcon k="symbol" />
              </th>
              <th
                className="text-left px-4 py-3 cursor-pointer hover:text-zinc-200 select-none hidden sm:table-cell"
                onClick={() => toggleSort('name')}
              >
                Name <SortIcon k="name" />
              </th>
              <th
                className="text-left px-4 py-3 cursor-pointer hover:text-zinc-200 select-none hidden md:table-cell"
                onClick={() => toggleSort('exchange')}
              >
                Exchange <SortIcon k="exchange" />
              </th>
              <th className="text-left px-4 py-3 hidden lg:table-cell text-zinc-400">Sector</th>
              <th
                className="text-right px-4 py-3 cursor-pointer hover:text-zinc-200 select-none"
                onClick={() => toggleSort('latest_price')}
              >
                Price <SortIcon k="latest_price" />
              </th>
              <th className="text-right px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {loading && stocks.length === 0 ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i} className="border-b border-zinc-800/50">
                  {[...Array(5)].map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-zinc-800 rounded animate-pulse" style={{ width: `${60 + Math.random() * 30}%` }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-16 text-zinc-600">
                  No stocks match your filters.
                </td>
              </tr>
            ) : (
              filtered.map((stock: StockSummary) => (
                <tr
                  key={`${stock.exchange}-${stock.symbol}`}
                  className="border-b border-zinc-800/50 hover:bg-zinc-800/40 transition"
                >
                  <td className="px-4 py-3">
                    <span className="font-mono text-emerald-400 font-semibold">
                      {stock.symbol}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-white hidden sm:table-cell">{stock.name}</td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <span className="bg-zinc-800 text-zinc-400 text-xs px-2 py-0.5 rounded font-mono">
                      {stock.exchange}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-zinc-500 hidden lg:table-cell">
                    {stock.sector ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-white">
                    {stock.latest_price != null
                      ? stock.latest_price.toLocaleString('en-KE', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/stocks/${stock.symbol}`}
                      className="text-xs text-emerald-400 hover:text-emerald-300 font-medium transition"
                    >
                      View →
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-zinc-800 flex items-center justify-between">
          <span className="text-zinc-600 text-xs">
            {filtered.length} of {stocks.length} securities
          </span>
          <span className="text-zinc-700 text-xs">
            Auto-refreshes every 30 s · Data for informational purposes only
          </span>
        </div>
      </div>
    </div>
  )
}