/**
 * Vestora API client
 * All requests attach JWT from localStorage.
 * All market/analytics responses include a disclaimer field — surface it in UI.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("vestora_token");
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail ?? `Request failed: ${res.status}`);
  }

  return res.json();
}

// ── Auth ──────────────────────────────────────────────

export const authApi = {
  login:    (email: string, password: string) =>
    request<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      body: new URLSearchParams({ username: email, password }),
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    }),

  register: (email: string, password: string, full_name: string) =>
    request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),
};

// ── Market ────────────────────────────────────────────

export const marketApi = {
  stocks:   (exchange = "NSE", sector?: string) =>
    request(`/api/market/stocks?exchange=${exchange}${sector ? `&sector=${sector}` : ""}`),

  stock:    (symbol: string, exchange = "NSE", days = 90) =>
    request(`/api/market/stocks/${symbol}?exchange=${exchange}&days=${days}`),

  forecast: (symbol: string, exchange = "NSE", horizon = 5) =>
    request(`/api/market/forecast/${symbol}?exchange=${exchange}&horizon=${horizon}`),

  anomalies:(exchange = "NSE", days = 7) =>
    request(`/api/market/anomalies?exchange=${exchange}&days=${days}`),
};

// ── Portfolio ─────────────────────────────────────────

export const portfolioApi = {
  get:    () => request("/api/portfolio"),
  add:    (symbol: string, quantity: number, avg_price: number) =>
    request("/api/portfolio", {
      method: "POST",
      body: JSON.stringify({ symbol, quantity, avg_price }),
    }),
  remove: (id: string) =>
    request(`/api/portfolio/${id}`, { method: "DELETE" }),
};

// ── Analytics ─────────────────────────────────────────

export const analyticsApi = {
  query: (query: string, context?: Record<string, unknown>) =>
    request("/api/ai/analytics", {
      method: "POST",
      body: JSON.stringify({ query, context }),
    }),
};