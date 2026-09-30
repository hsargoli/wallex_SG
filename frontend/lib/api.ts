import axios from "axios";

// استفاده از Next.js rewrite که توی next.config.ts تعریف کردیم
// /api/backend/* → http://127.0.0.1:8000/*
const client = axios.create({
  baseURL: "/api/backend",
  headers: { "Content-Type": "application/json" },
});

// ---------- Types ----------

export interface BudgetStatus {
  allocated_budget: string;
  in_use_capital: string;
  available_for_trade: string;
  currency: string;
}

export interface Market {
  symbol: string;
  base_asset: string;
  quote_asset: string;
  last_price: string | null;
}

export interface MarketsResponse {
  count: number;
  items: Market[];
}

export interface OrderBookLevel {
  price: string;
  quantity: string;
  sum: string;
}

export interface OrderBookResponse {
  symbol: string;
  best_bid: string | null;
  best_ask: string | null;
  spread: string | null;
  spread_pct: string | null;
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
}

export interface WalletBalance {
  asset: string;
  available: string;
  locked: string;
  total: string;
  fa_name: string | null;
  en_name: string | null;
}

export interface WalletResponse {
  count: number;
  items: WalletBalance[];
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

export interface PortfolioItem {
  asset: string;
  fa_name: string | null;
  available: string;
  locked: string;
  total: string;
  price_usdt_bid: string | null;
  price_usdt_last: string | null;
  price_tmn_bid: string | null;
  price_tmn_last: string | null;
  value_usdt_bid: string | null;
  value_usdt_last: string | null;
  value_tmn_bid: string | null;
  value_tmn_last: string | null;
  share_pct_bid: string;
  share_pct_last: string;
  has_tmn_pair: boolean;
  has_usdt_pair: boolean;
}

export interface PortfolioResponse {
  count: number;
  total_value_tmn_bid: string;
  total_value_tmn_last: string;
  total_value_usdt_bid: string;
  total_value_usdt_last: string;
  usdt_tmn_rate: string | null;
  items: PortfolioItem[];
}

// ---------- API methods ----------

export const api = {
  health: () =>
    client.get<{ status: string }>("/health").then((r) => r.data),

  // Budget
  getBudget: () =>
    client.get<BudgetStatus>("/v1/bot/budget").then((r) => r.data),
  setBudget: (amount: number) =>
    client
      .post<BudgetStatus>("/v1/bot/budget", { allocated_budget: amount })
      .then((r) => r.data),

  // Markets
  listMarkets: () =>
    client.get<MarketsResponse>("/v1/markets").then((r) => r.data),
  getOrderBook: (symbol: string) =>
    client
      .get<OrderBookResponse>(`/v1/markets/orderbook/${symbol}`)
      .then((r) => r.data),

  // Profitability
  evaluateProfitability: (payload: ProfitabilityRequest) =>
    client
      .post<ProfitabilityResponse>("/v1/profitability/evaluate", payload)
      .then((r) => r.data),

  // Wallet
  getWalletBalances: () =>
    client.get<WalletResponse>("/v1/account/balances").then((r) => r.data),

  // Portfolio
  getPortfolio: () =>
    client.get<PortfolioResponse>("/v1/account/portfolio").then((r) => r.data),
};
