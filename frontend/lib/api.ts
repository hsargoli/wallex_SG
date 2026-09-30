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
  fa_name: string | null;
  en_name: string | null;
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

// ---------- Candle Types ----------

export type Timeframe = "15m" | "1h" | "4h" | "1D";

export interface Candle {
  time: number;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
}

export interface CandlesResponse {
  symbol: string;
  timeframe: Timeframe;
  count: number;
  candles: Candle[];
}

// ---------- Signal Types ----------

export type SignalType = "buy" | "sell" | "hold";
export type SignalStrength = "weak" | "medium" | "strong";

export interface SignalRule {
  name: string;
  passed: boolean;
  score: number;
  reason: string;
}

export interface SignalResponse {
  symbol: string;
  timeframe: string;
  signal: SignalType;
  strength: SignalStrength;
  confidence: number;
  current_price: string;
  reasons: string[];
  rules: SignalRule[];
  buy_score: number;
  sell_score: number;
  stop_loss: string | null;
  take_profit: string | null;
  risk_reward: string | null;
  indicators: Record<string, string | null>;
}

export interface MultiTfSignal {
  signal: SignalType | "no_data" | "error";
  strength?: SignalStrength;
  confidence?: number;
  reasons?: string[];
  message?: string;
}

export interface Confluence {
  status: string;
  label: string;
  buy_count: number;
  sell_count: number;
  hold_count: number;
}

export interface MultiTfResponse {
  symbol: string;
  timeframes: Record<string, MultiTfSignal>;
  confluence: Confluence;
}

// ---------- Levels Types ----------

export interface PivotLevels {
  pp: string;
  r1: string;
  r2: string;
  r3: string;
  s1: string;
  s2: string;
  s3: string;
  basis_high: string;
  basis_low: string;
  basis_close: string;
}

export interface SwingLevel {
  price: string;
  type: "support" | "resistance";
  touches: number;
  last_time: number;
  strength: "weak" | "medium" | "strong";
  distance_pct: string;
}

export interface LevelsResponse {
  symbol: string;
  timeframe: string;
  current_price: string;
  pivot: PivotLevels | null;
  swings: SwingLevel[];
}

// ---------- Indicators Types ----------

export interface IndicatorsResponse {
  symbol: string;
  timeframe: string;
  count: number;
  candles: Array<{
    time: number;
    open: string;
    high: string;
    low: string;
    close: string;
    volume: string;
  }>;
  sma_20: (string | null)[];
  sma_50: (string | null)[];
  ema_9: (string | null)[];
  ema_21: (string | null)[];
  rsi_14: (string | null)[];
  volume_ma_20: (string | null)[];
  macd: (string | null)[];
  macd_signal: (string | null)[];
  macd_hist: (string | null)[];
  bb_upper: (string | null)[];
  bb_middle: (string | null)[];
  bb_lower: (string | null)[];
  atr_14: (string | null)[];
}

// ---------- Scanner Types ----------

export interface TrendResult {
  symbol: string;
  current_price: string;
  trend_score: number;
  direction: "bullish" | "bearish" | "neutral";
  strength: "weak" | "medium" | "strong";
  pattern: "trending" | "choppy" | "ranging";
  volatility_pct: string;
  ema_alignment: "aligned" | "mixed" | "counter";
  reasons: string[];
  change_3h: string | null;
  change_12h: string | null;
  change_24h: string | null;
  signal: "buy" | "sell" | "hold";
  risk_reward: string | null;
  sparkline: number[];
}

export interface ScannerListMeta {
  symbol: string;
  quote: string;
  daily_volume: string;
}

export interface ScannerListResponse {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  quote: string;
  symbols: string[];
  items_meta: ScannerListMeta[];
}

export interface ScannerScanResponse {
  count: number;
  items: TrendResult[];
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
  getCandles: (symbol: string, timeframe: Timeframe, limit = 500) =>
    client
      .get<CandlesResponse>(`/v1/markets/candles/${symbol}`, {
        params: { tf: timeframe, limit },
      })
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

  // Signals
  getSignal: (symbol: string, timeframe: string = "1h") =>
    client
      .get<SignalResponse>(`/v1/signals/${symbol}`, {
        params: { tf: timeframe },
      })
      .then((r) => r.data),
  getMultiTfSignals: (symbol: string) =>
    client
      .get<MultiTfResponse>(`/v1/signals/${symbol}/multi`)
      .then((r) => r.data),
  getLevels: (symbol: string, timeframe: string = "1h") =>
    client
      .get<LevelsResponse>(`/v1/signals/levels/${symbol}`, {
        params: { tf: timeframe },
      })
      .then((r) => r.data),
  getIndicators: (symbol: string, timeframe: string = "1h", limit: number = 500) =>
    client
      .get<IndicatorsResponse>(`/v1/signals/indicators/${symbol}`, {
        params: { tf: timeframe, limit },
      })
      .then((r) => r.data),

  // Scanner
  getScannerList: (page: number = 1, pageSize: number = 15, quote: string = "TMN") =>
    client
      .get<ScannerListResponse>("/v1/scanner/list", {
        params: { page, page_size: pageSize, quote },
      })
      .then((r) => r.data),
  scanSymbols: (symbols: string[]) =>
    client
      .get<ScannerScanResponse>("/v1/scanner/scan", {
        params: { symbols: symbols.join(",") },
      })
      .then((r) => r.data),
};
