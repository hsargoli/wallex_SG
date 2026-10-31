/**
 * Paper Trading — shared types (DRY ManualOrderForm).
 * Extracted from /guest and /paper-trading/manual pages.
 */

export type PaperPosition = {
  symbol: string;
  side: "BUY" | "SELL";
  entry_price: number;
  quantity: number;
  tp?: number | null;
  sl?: number | null;
  entry_time?: number;
  entry_idx?: number;
  reason?: string;
};

export type PaperTrade = {
  symbol: string;
  side: "BUY" | "SELL";
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  reason: string;
  entry_time?: number;
  exit_time?: number;
};

export type PaperStatus = {
  is_running: boolean;
  capital?: number;
  equity?: number;
  total_pnl?: number;
  total_pnl_pct?: number;
  win_rate?: number;
  trades_count?: number;
  open_positions?: PaperPosition[];
  recent_trades?: PaperTrade[];
  last_check_at?: number;
  check_count?: number;
  config?: {
    check_interval_sec?: number;
  };
};

export type OrderPayload = {
  symbol: string;
  side: "BUY" | "SELL";
  amount: number;
  tp?: number | null;
  sl?: number | null;
};
