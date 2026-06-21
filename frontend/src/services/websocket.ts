import { useAuthStore } from '../lib/authStore'

export type WsMessageType =
  | 'quote_update'
  | 'anomaly_alert'
  | 'forecast_ready'
  | 'ping'
  | 'pong'
  | 'error'

export interface WsMessage<T = unknown> {
  type: WsMessageType
  payload: T
  ts: string // ISO timestamp from server
}

export interface QuoteUpdatePayload {
  symbol: string
  exchange: string
  close: number
  change_pct: number | null
  volume: number | null
  date: string
}

export interface AnomalyAlertPayload {
  symbol: string
  exchange: string
  anomaly_type: string
  anomaly_score: number
  description: string
}

type MessageHandler<T = unknown> = (msg: WsMessage<T>) => void

const WS_BASE =
  (import.meta as any).env?.VITE_WS_URL ??
  (typeof window !== 'undefined'
    ? window.location.origin.replace(/^http/, 'ws')
    : 'ws://localhost:8000')

class VestoraWebSocket {
  private ws: WebSocket | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectDelay = 2_000
  private maxDelay = 30_000
  private handlers = new Map<WsMessageType | '*', Set<MessageHandler<any>>>()
  private subscriptions = new Set<string>()
  private intentionallyClosed = false

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return

    const token = useAuthStore.getState().token
    const url = token
      ? `${WS_BASE}/ws/market?token=${token}`
      : `${WS_BASE}/ws/market`

    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this.reconnectDelay = 2_000
      // Re-subscribe to any symbols that were active before reconnect
      this.subscriptions.forEach((symbol) => this._sendSubscribe(symbol))
    }

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const msg: WsMessage = JSON.parse(event.data)
        if (msg.type === 'ping') {
          this._send({ type: 'pong', payload: null, ts: new Date().toISOString() })
          return
        }
        this._dispatch(msg)
      } catch {
        // ignore malformed frames
      }
    }

    this.ws.onclose = () => {
      if (!this.intentionallyClosed) this._scheduleReconnect()
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  disconnect(): void {
    this.intentionallyClosed = true
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.ws?.close()
    this.ws = null
  }

  subscribe(symbol: string): void {
    this.subscriptions.add(symbol)
    this._sendSubscribe(symbol)
  }

  unsubscribe(symbol: string): void {
    this.subscriptions.delete(symbol)
    this._send({ type: 'unsubscribe' as any, payload: { symbol }, ts: new Date().toISOString() })
  }

  on<T = unknown>(type: WsMessageType | '*', handler: MessageHandler<T>): () => void {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set())
    this.handlers.get(type)!.add(handler as MessageHandler)
    // Return unsubscribe function
    return () => this.off(type, handler)
  }

  off<T = unknown>(type: WsMessageType | '*', handler: MessageHandler<T>): void {
    this.handlers.get(type)?.delete(handler as MessageHandler)
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  private _send(msg: object): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg))
    }
  }

  private _sendSubscribe(symbol: string): void {
    this._send({ type: 'subscribe', payload: { symbol }, ts: new Date().toISOString() })
  }

  private _dispatch(msg: WsMessage): void {
    this.handlers.get(msg.type)?.forEach((h) => h(msg))
    this.handlers.get('*')?.forEach((h) => h(msg))
  }

  private _scheduleReconnect(): void {
    this.reconnectTimer = setTimeout(() => {
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxDelay)
      this.connect()
    }, this.reconnectDelay)
  }
}

// Singleton — import and use anywhere
export const wsClient = new VestoraWebSocket()