// ── Market ────────────────────────────────────────────

export type Exchange = "NSE" | "USE" | "DSE" | "RSE";

export interface StockQuote {
  symbol:               string;
  name:                 string;
  exchange:             Exchange;
  close:                number;
  volume:               number | null;
  change_pct:           number | null;
  date:                 string;
  data_quality_warning: string | null;
}

export interface ForecastResult {
  symbol:              string;
  exchange:            Exchange;
  forecast_date:       string;
  horizon_days:        number;
  directional_signal:  "bullish" | "bearish" | "neutral";
  probability_up:      number;
  forecast_return_pct: number;
  ci_low:              number;
  ci_high:             number;
  model_version:       string;
  model_accuracy_30d:  number;
  disclaimer:          string;
}

export interface AnomalyFlag {
  symbol:        string;
  exchange:      Exchange;
  date:          string;
  anomaly_type:  "volume_spike" | "price_gap" | "overnight_gap" | "composite";
  anomaly_score: number;
  description:   string;
  disclaimer:    string;
}

// ── Portfolio ─────────────────────────────────────────

export interface PortfolioPosition {
  id:          string;
  symbol:      string;
  exchange:    Exchange;
  quantity:    number;
  avg_price:   number;
  current_price: number | null;
  pnl_pct:     number | null;
}

// ── Analytics ─────────────────────────────────────────

export interface AnalyticsResponse {
  answer:     string;
  sources:    string[];
  disclaimer: string;
}

// ── Auth ──────────────────────────────────────────────

export interface User {
  id:        string;
  email:     string;
  full_name: string | null;
  tier:      "free" | "premium" | "b2b";
}