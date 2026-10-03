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

  // ---------- Orders ----------
  listOrders: (symbol?: string) =>
    client
      .get<OrdersListResponse>("/v1/orders", {
        params: symbol ? { symbol } : undefined,
      })
      .then((r) => r.data),

  placeOrder: (payload: PlaceOrderRequest) =>
    client
      .post<Order>("/v1/orders/place", payload)
      .then((r) => r.data),

  cancelOrder: (clientId: string, symbol: string) =>
    client
      .delete<Order>(`/v1/orders/cancel/${clientId}`, {
        params: { symbol },
      })
      .then((r) => r.data),
};

// --- Simulation API ---

export interface DateItem {
  gregorian: string;       // 2026-10-02
  jalali: string;          // 1405/07/10
  jalali_pretty: string;   // 10 مهر 1405
}

export interface BotOption {
  slug: string;
  name: string;
  name_en: string;
  description: string;
  tags: string[];
  capabilities: string[];
  experimental?: boolean;
  warning?: string;
}

export interface BotsResponse {
  count: number;
  bots: BotOption[];
}

export interface SymbolOption {
  symbol: string;
  base: string;
  name_fa: string;
  name_en: string;
}

export interface CompareResultItem {
  bot_slug: string;
  bot_name: string;
  name_en: string;
  experimental: boolean;
  warning: string;
  status: string;
  total_trades: number;
  win_rate: number;
  pnl_pct: number;
  final_balance: number;
  total_pnl: number;
  error: string;
}

export interface CompareResponse {
  symbol: string;
  dates: {
    start: DateItem;
    end: DateItem;
  };
  results: CompareResultItem[];
}

export interface SymbolsResponse {
  count: number;
  symbols: SymbolOption[];
}

export interface SimulationTrade {
  i: number;
  side: "BUY" | "SELL";
  price: number;
  forced?: boolean;   // true یعنی در پایان شبیه‌سازی به‌اجبار بسته شده
}

export interface SimulationResult {
  status: string;
  symbol?: string;
  bot_slug?: string;
  prices_count?: number;
  trades?: SimulationTrade[];
  pnl_report: {
    initial_balance?: number;
    final_balance: number;
    total_pnl: number;
  };
  dates?: {
    start: DateItem;
    end: DateItem;
  };
}

export const runSimulation = async (
  startDate: string,
  endDate: string,
  symbol: string = "BTCUSDT",
  botSlug: string = "",
  initialBalance: number = 1000,
): Promise<SimulationResult> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const url = new URL(`${baseUrl}/v1/simulation/run`);
  url.searchParams.set("start_date", startDate);
  url.searchParams.set("end_date", endDate);
  url.searchParams.set("symbol", symbol);
  url.searchParams.set("initial_balance", String(initialBalance));
  if (botSlug) {
    url.searchParams.set("bot_slug", botSlug);
  }

  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Simulation failed: ${response.statusText}`);
  }
  return response.json();
};

export const getSimulationBots = async (): Promise<BotsResponse> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const response = await fetch(`${baseUrl}/v1/simulation/bots`);
  if (!response.ok) {
    return { count: 0, bots: [] };
  }
  return response.json();
};

export const getSimulationSymbols = async (): Promise<SymbolsResponse> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const response = await fetch(`${baseUrl}/v1/simulation/symbols`);
  if (!response.ok) {
    return { count: 0, symbols: [] };
  }
  return response.json();
};

export const compareAllBots = async (
  startDate: string,
  endDate: string,
  symbol: string = "BTCUSDT",
  initialBalance: number = 1000,
): Promise<CompareResponse> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const url = new URL(`${baseUrl}/v1/simulation/compare`);
  url.searchParams.set("start_date", startDate);
  url.searchParams.set("end_date", endDate);
  url.searchParams.set("symbol", symbol);
  url.searchParams.set("initial_balance", String(initialBalance));

  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Compare failed: ${response.statusText}`);
  }
  return response.json();
};

export const getSimulationAvailableDates = async (days: number = 90): Promise<DateItem[]> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const response = await fetch(`${baseUrl}/v1/simulation/available-dates?days=${days}`);
  if (!response.ok) {
    return [
      { gregorian: "2026-09-01", jalali: "1405/06/10", jalali_pretty: "10 شهریور 1405" },
      { gregorian: "2026-09-02", jalali: "1405/06/11", jalali_pretty: "11 شهریور 1405" },
      { gregorian: "2026-09-03", jalali: "1405/06/12", jalali_pretty: "12 شهریور 1405" },
    ];
  }
  const data = await response.json();
  return data.dates || [];
};

// ---------- Order Types ----------

export type OrderSide = "BUY" | "SELL";
export type TradingOrderType = "LIMIT" | "MARKET" | "STOP_LIMIT" | "STOP_MARKET";
export type OrderStatus =
  | "NEW"
  | "PARTIALLY_FILLED"
  | "FILLED"
  | "CANCELED"
  | "REJECTED"
  | "EXPIRED"
  | "UNKNOWN";

export interface Order {
  client_id: string;
  symbol: string;
  side: OrderSide;
  type: TradingOrderType;
  status: OrderStatus;
  price: string;
  orig_qty: string;
  executed_qty: string;
  executed_price: string;
  executed_sum: string;
  fee: string;
  active: boolean;
  executed_percent: string;
  created_at: number;
  updated_at: number;
}

export interface OrdersListResponse {
  count: number;
  orders: Order[];
}

export interface PlaceOrderRequest {
  symbol: string;
  side: OrderSide;
  type: TradingOrderType;
  quantity: string;
  price?: string;
  stop_price?: string;
  client_id?: string;
}
