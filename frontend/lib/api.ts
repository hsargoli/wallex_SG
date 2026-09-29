/**
 * Type-safe API client for the Wallex backend.
 */

const API_BASE = "/api/backend";

// ---------- Types ----------

export interface BudgetStatus {
  allocated_budget: string;
  in_use_capital: string;
  available_for_trade: string;
  currency: string;
}

export interface OrderBookLevel {
  price: string;
  quantity: string;
  sum: string;
}

export interface OrderBookResponse {
  symbol: string;
  best_bid: string;
  best_ask: string;
  spread: string;
  spread_pct: string;
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
}

export type OrderType = "maker" | "taker";

export interface ProfitabilityRequest {
  symbol: string;
  order_type: OrderType;
  capital: number;
  slippage_pct?: number;
  maker_fee_rate?: number;
  taker_fee_rate?: number;
}

export interface ProfitabilityResponse {
  symbol: string;
  order_type: OrderType;
  best_bid: string;
  best_ask: string;
  spread: string;
  spread_pct: string;
  capital: string;
  applied_fee_rate: string;
  slippage_pct: string;
  effective_buy_price: string;
  effective_sell_price: string;
  gross_profit: string;
  buy_fee: string;
  sell_fee: string;
  slippage_cost: string;
  total_cost: string;
  net_profit: string;
  net_profit_pct: string;
  min_profitable_spread: string;
  is_profitable: boolean;
  notes: string[];
}

export interface Market {
  symbol: string;
  base_asset: string;
  quote_asset: string;
  fa_name?: string;
  en_name?: string;
  base_precision?: number;
  quote_precision?: number;
}

// ---------- Error handling ----------

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(`${status}: ${detail}`);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }

  return res.json() as Promise<T>;
}

// ---------- Endpoints ----------

export const api = {
  health: () => request<{ status: string }>("/health"),

  getBudget: () => request<BudgetStatus>("/v1/bot/budget"),
  setBudget: (amount: number) =>
    request<BudgetStatus>("/v1/bot/budget", {
      method: "POST",
      body: JSON.stringify({ allocated_budget: amount }),
    }),

  listMarkets: () =>
    request<{ count: number; items: Market[] }>("/v1/markets"),
  getMarket: (symbol: string) => request<Market>(`/v1/markets/${symbol}`),
  getOrderBook: (symbol: string) =>
    request<OrderBookResponse>(`/v1/markets/orderbook/${symbol}`),

  evaluateProfitability: (payload: ProfitabilityRequest) =>
    request<ProfitabilityResponse>("/v1/profitability/evaluate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
