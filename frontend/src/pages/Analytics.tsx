import { useState, useRef } from 'react'
import { aiApi } from '../lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  disclaimer?: string
  ts: Date
}

const SUGGESTED = [
  'What is the outlook for Safaricom stock this month?',
  'Explain the risk profile of the NSE 20 index.',
  'Which East African sectors show the most momentum?',
  'How should I think about USE equities vs NSE equities?',
  'What factors drive volatility in EAC capital markets?',
]

export default function Analytics() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  const send = async (query: string) => {
    const q = query.trim()
    if (!q || loading) return
    setError(null)
    setInput('')

    const userMsg: Message = { role: 'user', content: q, ts: new Date() }
    setMessages((prev) => [...prev, userMsg])

    setLoading(true)
    try {
      const { data } = await aiApi.query(q)
      const assistantMsg: Message = {
        role: 'assistant',
        content: data.response,
        disclaimer: data.disclaimer,
        ts: new Date(),
      }
      setMessages((prev) => [...prev, assistantMsg])
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'AI query failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    send(input)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="mb-6 shrink-0">
        <h1 className="text-white text-2xl font-bold">Analytics</h1>
        <p className="text-zinc-500 text-sm mt-0.5">
          AI-powered market intelligence · East African capital markets
        </p>
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center gap-6">
            <div>
              <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <p className="text-zinc-400 text-sm mb-1">Ask anything about East African markets</p>
              <p className="text-zinc-600 text-xs">Powered by Vestora AI · NSE, USE, DSE, RSE data</p>
            </div>

            <div className="w-full max-w-lg">
              <p className="text-zinc-600 text-xs uppercase tracking-wider mb-3">Suggested queries</p>
              <div className="flex flex-col gap-2">
                {SUGGESTED.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="text-left text-sm text-zinc-400 hover:text-white bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 rounded-lg px-4 py-2.5 transition"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center shrink-0 mt-0.5">
                    <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                )}

                <div className={`max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                  <div
                    className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-emerald-500/20 border border-emerald-500/30 text-white rounded-tr-sm'
                        : 'bg-zinc-900 border border-zinc-800 text-zinc-200 rounded-tl-sm'
                    }`}
                  >
                    {msg.content}
                  </div>
                  {msg.disclaimer && (
                    <p className="text-zinc-700 text-xs px-1">{msg.disclaimer}</p>
                  )}
                  <p className="text-zinc-700 text-[10px] px-1">
                    {msg.ts.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-3 justify-start">
                <div className="w-7 h-7 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center shrink-0">
                  <svg className="w-3.5 h-3.5 text-emerald-400 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-2xl rounded-tl-sm px-4 py-3 flex gap-1 items-center">
                  {[0, 1, 2].map((d) => (
                    <span
                      key={d}
                      className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce"
                      style={{ animationDelay: `${d * 150}ms` }}
                    />
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3 text-red-400 text-sm">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="shrink-0">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about NSE, USE, sector trends, stock analysis…"
            disabled={loading}
            className="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3 text-white placeholder-zinc-600 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/30 transition disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-emerald-500 hover:bg-emerald-400 disabled:bg-zinc-800 disabled:text-zinc-600 text-black font-semibold px-5 py-3 rounded-xl transition text-sm"
          >
            Send
          </button>
        </div>
        <p className="text-zinc-700 text-xs mt-2 text-center">
          AI responses are informational only and do not constitute investment advice.
        </p>
      </form>
    </div>
  )
}