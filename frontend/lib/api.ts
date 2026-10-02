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

// ---------- Paper V2 Types ----------

export interface PaperPosition {
  symbol: string;
  strategy: string;
  entry_price: number;
  quantity: number;
  tp: number;
  sl: number;
  entry_time: number;
  entry_idx: number;
  reason: string;
}

export interface PaperTrade {
  symbol: string;
  strategy: string;
  entry_time: number;
  exit_time: number;
  entry_price: number;
  exit_price: number;
  pnl_pct: number;
  pnl_tmn: number;
  exit_reason: string;
  duration_minutes: number;
}

export interface EquityPoint {
  time: number;
  capital: number;
}

export interface PaperV2Status {
  is_running: boolean;
  started_at: number;
  runtime_minutes: number;
  initial_capital: number;
  current_capital: number;
  total_return_pct: number;
  profit_tmn: number;
  max_drawdown_pct: number;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  open_positions: PaperPosition[];
  recent_trades: PaperTrade[];
  equity_curve: EquityPoint[];
  last_check_time: number;
  active_symbols: string[];
  config: Record<string, unknown>;
}

// ---------- Paper V2 Types ----------

export interface PaperPosition {
  symbol: string;
  strategy: string;
  entry_price: number;
  quantity: number;
  tp: number;
  sl: number;
  entry_time: number;
  entry_idx: number;
  reason: string;
}

export interface PaperTrade {
  symbol: string;
  strategy: string;
  entry_time: number;
  exit_time: number;
  entry_price: number;
  exit_price: number;
  pnl_pct: number;
  pnl_tmn: number;
  exit_reason: string;
  duration_minutes: number;
}

export interface EquityPoint {
  time: number;
  capital: number;
}

export interface PaperV2Status {
  is_running: boolean;
  started_at: number;
  runtime_minutes: number;
  initial_capital: number;
  current_capital: number;
  total_return_pct: number;
  profit_tmn: number;
  max_drawdown_pct: number;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  open_positions: PaperPosition[];
  recent_trades: PaperTrade[];
  equity_curve: EquityPoint[];
  last_check_time: number;
  active_symbols: string[];
  config: Record<string, unknown>;
}

// ---------- Bot Types ----------

export interface BotInfo {
  slug: string;
  name: string;
  name_en: string;
  version: string;
  description: string;
  tags: string[];
  capabilities: string[];
  author: string;
  status?: "idle" | "running" | "stopped" | "error";
}

export interface BotsListResponse {
  count: number;
  bots: BotInfo[];
}

export interface BotStatusResponse {
  is_running: boolean;
  started_at?: number;
  runtime_minutes?: number;
  initial_capital?: number;
  current_capital?: number;
  total_return_pct?: number;
  profit_tmn?: number;
  max_drawdown_pct?: number;
  total_trades?: number;
  wins?: number;
  losses?: number;
  win_rate?: number;
  open_positions?: Array<{
    symbol: string;
    strategy: string;
    entry_price: number;
    tp: number;
    sl: number;
    reason: string;
  }>;
  recent_trades?: Array<{
    symbol: string;
    strategy: string;
    pnl_pct: number;
    pnl_tmn: number;
    exit_reason: string;
  }>;
  active_symbols?: string[];
  [key: string]: unknown;
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
  // Paper V2
  getPaperV2Status: () =>
    client.get<PaperV2Status>("/v1/paper-v2/status").then((r) => r.data),
  startPaperV2: () =>
    client.post("/v1/paper-v2/start").then((r) => r.data),
  stopPaperV2: () =>
    client.post("/v1/paper-v2/stop").then((r) => r.data),
  resetPaperV2: () =>
    client.post("/v1/paper-v2/reset").then((r) => r.data),

  // Bots
  listBots: () =>
    client.get<BotsListResponse>("/v1/bots").then((r) => r.data),
  getBot: (slug: string) =>
    client.get<BotInfo>(`/v1/bots/${slug}`).then((r) => r.data),
  getBotStatus: (slug: string) =>
    client.get<BotStatusResponse>(`/v1/bots/${slug}/status`).then((r) => r.data),
  startBot: (slug: string) =>
    client.post(`/v1/bots/${slug}/start`).then((r) => r.data),
  stopBot: (slug: string) =>
    client.post(`/v1/bots/${slug}/stop`).then((r) => r.data),
  resetBot: (slug: string) =>
    client.post(`/v1/bots/${slug}/reset`).then((r) => r.data),
};

// --- Simulation API ---
export interface SimulationResult {
  status: string;
  pnl_report: {
    final_balance: number;
    total_pnl: number;
  };
}

export const runSimulation = async (startDate: string, endDate: string): Promise<SimulationResult> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const response = await fetch(`${baseUrl}/v1/simulation/run?start_date=${startDate}&end_date=${endDate}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok) {
    throw new Error(`Simulation failed: ${response.statusText}`);
  }
  return response.json();
};

export const getSimulationAvailableDates = async (): Promise<string[]> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const response = await fetch(`${baseUrl}/v1/simulation/available-dates`);
  if (!response.ok) return ["2026-09-01", "2026-09-02", "2026-09-03"];
  const data = await response.json();
  return data.dates || [];
};
