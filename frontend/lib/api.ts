import axios from "axios";
import { getUserToken } from "./auth";
import { getGuestToken } from "./guest";

// استفاده از Next.js rewrite که توی next.config.ts تعریف کردیم
// /api/backend/* → http://127.0.0.1:8000/*
const client = axios.create({
  baseURL: "/api/backend",
  headers: { "Content-Type": "application/json" },
});

// Auth interceptor — اولویت: user-token → guest-token
client.interceptors.request.use((config) => {
  config.headers = config.headers ?? {};
  const headers = config.headers as Record<string, string>;

  const userToken = getUserToken();
  if (userToken) {
    headers["Authorization"] = `Bearer ${userToken}`;
    return config;
  }

  const guestToken = getGuestToken();
  if (guestToken) {
    headers["X-Guest-Token"] = guestToken;
  }
  return config;
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
  daily_volume: string | null;
  daily_quote_volume: string | null;
  daily_change_percent: string | null;
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

export interface SyntheticRange {
  from_ts: number;
  to_ts: number;
  source_tf: string;
}

export interface CandlesV2Response {
  symbol: string;
  timeframe: string;
  count: number;
  real_count: number;
  synthetic_count: number;
  candles: Candle[];
  synthetic_ranges: SyntheticRange[];
}

export interface PeriodFacts {
  period: string;
  timeframe: string;
  available: boolean;
  candles_count?: number;
  change_pct?: string;
  first_price?: string;
  last_price?: string;
  high_price?: string;
  high_time?: number;
  low_price?: string;
  low_time?: number;
  volatility_pct?: string;
  max_drop_pct?: string;
  max_rise_pct?: string;
  avg_range_pct?: string;
  daily_vol_pct?: string;
  pullback_count?: number;
  pullback_avg_pct?: string;
  swing_count?: number;
  biggest_rise_pct?: string;
  biggest_rise_time?: number;
  biggest_drop_pct_swing?: string;
  biggest_drop_time?: number;
  trend_direction?: string;
  trend_strength?: string;
  trend_pattern?: string;
  trend_score?: number;
  avg_volume?: string;
  volume_vs_avg?: string;
  facts?: string[];
  interpretation?: string;
}

export interface FactsSummary {
  overall_behavior: string;
  outlook: string;
  risk_level: string;
  advice: string;
  consistency: string;
}

export interface FactsResponse {
  symbol: string;
  periods: PeriodFacts[];
  summary?: FactsSummary;
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
  rsi_14: string | null;
  atr_14: string | null;
  atr_pct: string | null;
  ema_9: string | null;
  ema_21: string | null;
  ema_diff_pct: string | null;
  macd_hist: string | null;
  bb_pct: string | null;
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
  timeframe: string;
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
  getMarket: (symbol: string) =>
    client.get<Market>(`/v1/markets/${symbol}`).then((r) => r.data),
  getAnalysis: (symbol: string, timeframe: string = "1h") =>
    client.get<AnalysisResult>(`/v1/analysis/${symbol}?timeframe=${timeframe}`).then((r) => r.data),
  getNooaahStatus: (top: number = 5) =>
    client.get<NooaahStatusResponse>(`/v1/nooaah/status?top=${top}`).then((r) => r.data),
  getNooaahConfig: () =>
    client.get<NooaahConfigResponse>("/v1/nooaah/config").then((r) => r.data),
  updateNooaahConfig: (body: {
    mode?: string;
    capital_total?: number;
    daily_loss_limit_pct?: number;
  }) =>
    client.post<NooaahConfigResponse>("/v1/nooaah/config", body).then((r) => r.data),
  killNooaah: () =>
    client.post<NooaahConfigResponse>("/v1/nooaah/kill").then((r) => r.data),
  resumeNooaah: () =>
    client.post<NooaahConfigResponse>("/v1/nooaah/resume").then((r) => r.data),
  getNooaahReadiness: () =>
    client.get<NooaahReadinessResponse>("/v1/nooaah/readiness").then((r) => r.data),
  activateNooaahLive: (phrase: string) =>
    client.post<NooaahConfigResponse>("/v1/nooaah/live/activate", {
      confirmation_phrase: phrase,
    }).then((r) => r.data),
  pauseNooaahLive: (reason: string = "manual") =>
    client.post<NooaahConfigResponse>(`/v1/nooaah/live/pause?reason=${reason}`).then((r) => r.data),
  advanceNooaahStage: () =>
    client.post<NooaahConfigResponse>("/v1/nooaah/live/stage/advance").then((r) => r.data),
  getNooaahLiveDraft: () =>
    client.get<NooaahDraftResponse>("/v1/nooaah/live/draft").then((r) => r.data),
  updateNooaahLiveDraft: (body: Record<string, unknown>) =>
    client.put<NooaahDraftResponse>("/v1/nooaah/live/draft", body).then((r) => r.data),
  clearNooaahLiveDraft: () =>
    client.delete<NooaahDraftResponse>("/v1/nooaah/live/draft").then((r) => r.data),
  getNooaahStopPreview: () =>
    client.get<NooaahStopPreviewResponse>("/v1/nooaah/live/stop/preview").then((r) => r.data),
  stopNooaahLive: (action: "sell" | "pause" | "kill") =>
    client.post<NooaahStopResultResponse>("/v1/nooaah/live/stop", { action }).then((r) => r.data),
  getNooaahCycles: (limit: number = 30) =>
    client.get<NooaahCycleLogResponse[]>(`/v1/nooaah/cycles?limit=${limit}`).then((r) => r.data),
  getNooaahBacktest: (params: {
    top?: number;
    limit?: number;
    symbols?: string;
    start?: string;
    end?: string;
    conf?: number;
    cc?: number;
    tp?: number;
    sl?: number;
    vol_z_min?: number;
  } = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) qs.set(k, String(v));
    });
    return client.get<NooaahBacktestResponse>(`/v1/nooaah/backtest?${qs}`).then((r) => r.data);
  },
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

  getCandlesV2: (symbol: string, timeframe: Timeframe, limit = 500) =>
    client
      .get<CandlesV2Response>(`/v1/markets/candles-v2/${symbol}`, {
        params: { tf: timeframe, limit },
      })
      .then((r) => r.data),

  getFacts: (symbol: string) =>
    client
      .get<FactsResponse>(`/v1/markets/facts/${symbol}`)
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

  // Cost Basis
  getCostBasis: () =>
    client.get<CostBasisResponse>("/v1/account/cost-basis").then((r) => r.data),

  // Market Overview
  getMarketOverview: (symbol: string, tf: string = "1h") =>
    client
      .get<MarketOverviewResponse>(`/v1/markets/overview/${symbol}`, {
        params: { tf },
      })
      .then((r) => r.data),

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
  getBatchSignals: (payload: BatchSignalsRequest) =>
    client
      .post<BatchSignalsResponse>("/v1/signals/batch", payload)
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
  scanSymbols: (symbols: string[], tf: string = "1h") =>
    client
      .get<ScannerScanResponse>("/v1/scanner/scan", {
        params: { symbols: symbols.join(","), tf },
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
  setBotTimeframe: (slug: string, timeframe: string) =>
    client.post(`/v1/bots/${slug}/timeframe`, { timeframe }).then((r) => r.data),
  setBotSymbols: (slug: string, symbols: string[]) =>
    client.post(`/v1/bots/${slug}/symbols`, { symbols }).then((r) => r.data),

  // ---------- Paper V3 ----------
  getPaperV3Status: () =>
    client.get("/v1/paper-v3/status").then((r) => r.data),
  getPaperV3Live: () =>
    client.get("/v1/paper-v3/live").then((r) => r.data),
  startPaperV3: (payload: any) =>
    client.post("/v1/paper-v3/start", payload).then((r) => r.data),
  stopPaperV3: () =>
    client.post("/v1/paper-v3/stop").then((r) => r.data),
  resetPaperV3: () =>
    client.post("/v1/paper-v3/reset").then((r) => r.data),

  // ---------- Orders ----------
  listOrders: (symbol?: string, status?: string) =>
    client
      .get<OrdersListResponse>("/v1/orders", {
        params: {
          ...(symbol ? { symbol } : {}),
          ...(status ? { status } : {}),
        },
      })
      .then((r) => r.data),

  listOpenOrders: (symbol?: string) =>
    client
      .get<OrdersListResponse>("/v1/orders/open", {
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

  // ---------- Bot Budgets ----------
  getTotalBudget: () =>
    client
      .get<TotalBudget>("/v1/bots/budgets/total")
      .then((r) => r.data),

  listBotBudgets: () =>
    client
      .get<BotBudgetListResponse>("/v1/bots/budgets")
      .then((r) => r.data),

  getBotBudget: (slug: string) =>
    client
      .get<BotBudget>(`/v1/bots/${slug}/budget`)
      .then((r) => r.data),

  setBotBudget: (slug: string, amount: number | string) =>
    client
      .post<BotBudget>(`/v1/bots/${slug}/budget`, {
        allocated: String(amount),
      })
      .then((r) => r.data),

  // ---------- Guest Mode ----------
  createGuest: () =>
    client
      .post<{ guest_token: string; capital_total: number; created_at: number }>(
        "/v1/guest/anonymous",
      )
      .then((r) => r.data),

  getGuestMe: () =>
    client
      .get<{
        guest_token: string;
        capital_total: number;
        created_at: number;
        last_seen_at: number;
      }>("/v1/guest/me")
      .then((r) => r.data),

  getGuestPaperV3Status: () =>
    client.get("/v1/guest/paper-v3/status").then((r) => r.data),

  getGuestPaperV3Live: () =>
    client.get("/v1/guest/paper-v3/live").then((r) => r.data),

  startGuestPaperV3: (payload?: unknown) =>
    client.post("/v1/guest/paper-v3/start", payload ?? {}).then((r) => r.data),

  stopGuestPaperV3: () =>
    client.post("/v1/guest/paper-v3/stop").then((r) => r.data),

  resetGuestPaperV3: () =>
    client.post("/v1/guest/paper-v3/reset").then((r) => r.data),

  placeGuestOrder: (payload: {
    side: "buy" | "sell";
    symbol: string;
    quantity?: number;
    amount_tmn?: number;
    limit_price?: number;
    tp_pct?: number;
    sl_pct?: number;
  }) =>
    client.post("/v1/guest/order", payload).then((r) => r.data),

  getGuestPrice: (symbol: string) =>
    client
      .get<{ symbol: string; price: number | null; error?: string }>(
        `/v1/guest/price/${symbol}`,
      )
      .then((r) => r.data),

  // ---------- Public (Guest-accessible) ----------
  getPublicSignals: (symbol: string, timeframe: string = "1h") =>
    client
      .get(`/v1/signals/${symbol}`, { params: { tf: timeframe } })
      .then((r) => r.data),

  getPublicScanner: (page: number = 1, pageSize: number = 8) =>
    client
      .get(`/v1/scanner/list`, {
        params: { page, page_size: pageSize, quote: "TMN" },
      })
      .then((r) => r.data),

  getPublicAnalysis: (symbol: string, timeframe: string = "1h") =>
    client
      .get(`/v1/analysis/${symbol}`, { params: { tf: timeframe } })
      .then((r) => r.data),

  getPublicMarketOverview: (symbol: string, timeframe: string = "1h") =>
    client
      .get(`/v1/markets/overview/${symbol}`, { params: { tf: timeframe } })
      .then((r) => r.data),

  // ---------- Auth ----------
  register: (payload: {
    email: string;
    password: string;
    guest_token?: string | null;
  }) =>
    client.post("/v1/auth/register", payload).then((r) => r.data),

  login: (payload: { email: string; password: string }) =>
    client.post("/v1/auth/login", payload).then((r) => r.data),

  getMe: () =>
    client.get("/v1/auth/me").then((r) => r.data),

  logout: () =>
    client.post("/v1/auth/logout").then((r) => r.data),

  closeGuestPosition: (symbol: string) =>
    client
      .post(`/v1/guest/position/${symbol}/close`)
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
  timeframe: string = "1h",
): Promise<SimulationResult> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const url = new URL(`${baseUrl}/v1/simulation/run`);
  url.searchParams.set("start_date", startDate);
  url.searchParams.set("end_date", endDate);
  url.searchParams.set("symbol", symbol);
  url.searchParams.set("initial_balance", String(initialBalance));
  url.searchParams.set("timeframe", timeframe);
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
  timeframe: string = "1h",
): Promise<CompareResponse> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const url = new URL(`${baseUrl}/v1/simulation/compare`);
  url.searchParams.set("start_date", startDate);
  url.searchParams.set("end_date", endDate);
  url.searchParams.set("symbol", symbol);
  url.searchParams.set("initial_balance", String(initialBalance));
  url.searchParams.set("timeframe", timeframe);

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
  stop_price: string;
  stop_price_condition: string;
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
  stop_price_condition?: "<=" | ">=";
  client_id?: string;
}

// ---------- Bot Budget Types ----------

export interface BotBudget {
  slug: string;
  allocated: string;
  in_use: string;
  free: string;
  usage_pct: number;
  currency: string;
}

export interface BotBudgetListResponse {
  count: number;
  items: BotBudget[];
}

export interface TotalBudget {
  total_budget: string;
  total_allocated: string;
  unallocated: string;
  total_in_use: string;
  available: string;
  allocated_budget: string;
  in_use_capital: string;
  available_for_trade: string;
  currency: string;
}

// ---------- Batch Signals Types ----------

export interface BatchSignalItem {
  symbol: string;
  signal: "buy" | "sell" | "hold";
  strength: "weak" | "medium" | "strong";
  confidence: number;
  current_price: string;
  reasons: string[];
  buy_score: number;
  sell_score: number;
  stop_loss: string | null;
  take_profit: string | null;
  risk_reward: string | null;
  sparkline: number[];
  change_24h: number | null;
  change_7d: number | null;
  change_1h: number | null;
  change_1m: number | null;
  change_1y: number | null;
  error?: string | null;
}

export interface BatchSignalsResponse {
  timeframe: string;
  count: number;
  signals: BatchSignalItem[];
}

export interface BatchSignalsRequest {
  symbols: string[];
  tf?: string;
  limit?: number;
}


// ─── Backtest (bot) ───
export interface BotBacktestParams {
  tf: string;
  top: number;
  initial_capital: number;
  position_size_pct: number;
  fee_pct: number;
  symbols?: string;
}

export interface BotBacktestResult {
  bot_slug: string;
  timeframe: string;
  symbols_source: string;
  symbols_requested: number;
  symbols_ok: number;
  failed: { symbol: string; error: string }[];
  summary: {
    total_trades: number;
    wins: number;
    losses: number;
    win_rate: number;
    avg_trade_pct: number;
    avg_symbol_pnl_pct: number;
    profit_factor: number | null;
    worst_symbol_dd_pct: number;
    reliable: boolean;
  };
  per_symbol: {
    symbol: string;
    candles: number;
    trades: number;
    win_rate: number;
    pnl_pct: number;
    profit_factor: number | null;
    max_drawdown_pct: number;
  }[];
  trades: {
    symbol: string;
    entry_time: number;
    exit_time: number;
    entry_price: number;
    exit_price: number;
    pnl: number;
    pnl_pct: number;
    exit_reason: string;
    duration_candles: number;
  }[];
}

export const runBotBacktest = async (
  botSlug: string,
  params: BotBacktestParams,
): Promise<BotBacktestResult> => {
  const res = await client.get("/v1/backtest/bot/" + botSlug, {
    params: { ...params, limit: 3000 },
    timeout: 120000,
  });
  return res.data;
};


export interface CompareBotsResult {
  timeframe: string;
  symbols: string;
  buy_hold_avg_pct: number;
  buy_hold_errors?: string[];
  bots: {
    bot_slug: string;
    error?: string;
    symbols_ok?: number;
    symbols_requested?: number;
    summary?: BotBacktestResult["summary"];
  }[];
}

export const compareBotsBacktest = async (params: {
  symbols: string;
  tf: string;
  initial_capital: number;
  fee_pct: number;
}): Promise<CompareBotsResult> => {
  const res = await client.get("/v1/backtest/compare", { params, timeout: 240000 });
  return res.data;
};


export const getTradingMode = async (): Promise<{ live_enabled: boolean; field: string }> => {
  const res = await client.get("/v1/orders/trading-mode");
  return res.data;
};


export interface ChaseStatus {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  status: string;
  dry_run: boolean;
  low: string;
  high: string;
  quantity: string;
  filled: string;
  moves: number;
  own_price: string | null;
  last_action: string;
  last_reason: string;
  errors: number;
  started_at: number;
  deadline_at: number;
  max_notional: string | null;
  log: { t: number; msg: string }[];
}

export interface ChaseCreate {
  symbol: string;
  side: "BUY" | "SELL";
  low: string;
  high: string;
  quantity: string;
  dry_run: boolean;
  max_notional: string | null;
}

export const chaseApi = {
  create: (body: ChaseCreate) =>
    client.post<ChaseStatus>("/v1/order-chase", body).then((r) => r.data),
  list: () =>
    client.get<{ items: ChaseStatus[] }>("/v1/order-chase").then((r) => r.data),
  stop: (id: string) =>
    client.post<ChaseStatus>(`/v1/order-chase/${id}/stop`).then((r) => r.data),
};


// ---------- Cost Basis ----------

export interface CostBasisItem {
  symbol: string;
  avg_buy_price: string;
  total_qty_bought: string;
  total_invested: string;
  orders_count: number;
  buy_count: number;
  sell_count: number;
}

export interface CostBasisResponse {
  count: number;
  items: CostBasisItem[];
}


// ---------- Market Overview ----------

export interface MarketOverviewChanges {
  h1: number | null;
  h24: number | null;
  d7: number | null;
  m1: number | null;
  m3: number | null;
  y1: number | null;
}

export interface MarketOverviewSignal {
  type: "buy" | "sell" | "hold";
  strength: "weak" | "medium" | "strong";
  confidence: number;
  reasons: string[];
  buy_score: number;
  sell_score: number;
  stop_loss: string | null;
  take_profit: string | null;
  risk_reward: string | null;
}

export interface MarketRange {
  max: string;
  min: string;
  change_pct: number;
}

export interface MarketOverviewStats {
  volume_24h: string | null;
  quote_volume_24h: string | null;
  high_24h: string | null;
  low_24h: string | null;
  volume_7d: string | null;
  bid: string | null;
  ask: string | null;
  bid_volume: string | null;
  ask_volume: string | null;
  bid_count: number | null;
  ask_count: number | null;
  trade_count: number | null;
  range_30d: MarketRange | null;
  range_90d: MarketRange | null;
  range_1y: MarketRange | null;
}

export interface MoneyFlow {
  buy_volume: string;
  sell_volume: string;
  buy_pct: number;
  sell_pct: number;
  buy_count: number;
  sell_count: number;
  total_trades: number;
  pressure: "strong_buy" | "buy" | "balanced" | "sell" | "strong_sell";
  pressure_fa: string;
  price_change_pct: number | null;
  combined:
    | "confirmed_bullish"
    | "divergence_resistance"
    | "confirmed_bearish"
    | "divergence_support"
    | "neutral";
  combined_fa: string;
}

export interface MoneyFlow {
  buy_volume: string;
  sell_volume: string;
  buy_pct: number;
  sell_pct: number;
  buy_count: number;
  sell_count: number;
  total_trades: number;
  pressure: "strong_buy" | "buy" | "balanced" | "sell" | "strong_sell";
  pressure_fa: string;
  price_change_pct: number | null;
  combined:
    | "confirmed_bullish"
    | "divergence_resistance"
    | "confirmed_bearish"
    | "divergence_support"
    | "neutral";
  combined_fa: string;
}

export interface CandleCountItem {
  total: number;
  green: number;
  red: number;
  doji: number;
  green_pct: number;
}

export interface CandleCount {
  h1: CandleCountItem | null;
  h24: CandleCountItem | null;
  d7: CandleCountItem | null;
  d30: CandleCountItem | null;
  y1: CandleCountItem | null;
}

export interface MarketOverviewResponse {
  symbol: string;
  timeframe: string;
  current_price: string;
  changes: MarketOverviewChanges;
  signal: MarketOverviewSignal;
  stats: MarketOverviewStats;
  money_flow: MoneyFlow | null;
  candle_count: CandleCount | null;
}

// ---------- end Market Overview ----------

// ---------- Analysis types ----------

export interface AnalysisRegimeCounts {
  trending_up: number;
  trending_down: number;
  ranging: number;
  choppy: number;
}

export interface AnalysisResult {
  symbol: string;
  timeframe: string;
  window_count: number;
  regime_counts: AnalysisRegimeCounts;
  dominant_regime: string | null;
  volatility_mean: number;
  volatility_std: number;
  rsi_mean: number;
  trend_mean: number;
}

// ---------- Nooaah types ----------

export interface NooaahProposal {
  symbol: string;
  action: string;
  entry: number;
  take_profit: number;
  stop_loss: number;
  confidence: number;
  regime: string;
  reason: string;
}

export interface NooaahStatusResponse {
  symbols_analyzed: string[];
  duration_seconds: number;
  proposal: NooaahProposal | null;
  error: string | null;
}

export interface NooaahTrade {
  entry_price: string;
  exit_price: string;
  side: string;
  return_pct: number;
  exit_reason: string;
  confidence: number;
  duration_candles: number;
}

export interface NooaahBacktestResponse {
  symbols: string[];
  candles_analyzed: number;
  signals_generated: number;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  total_return_pct: number;
  max_drawdown_pct: number;
  profit_factor: number;
  sharpe_ratio: number;
  avg_duration_candles: number;
  equity_curve_full: number[];
  buy_hold_curve: number[];
  recent_trades: NooaahTrade[];
}

// ---------- Nooaah Config type ----------

export interface NooaahConfigResponse {
  mode: string;
  capital_total: number;
  capital_available: number;
  capital_in_use: number;
  daily_loss_limit_pct: number;
  daily_pnl_pct: number;
  daily_loss_hit: boolean;
  killed: boolean;
  open_positions_count: number;
  closed_trades_count: number;
  last_run: number;
  scheduler_running: boolean;
  scheduler_last_status: string | null;
  live_stage: number;
  consecutive_losses: number;
  pause_reason: string;
  activated_live_at: number;
  paper_started_at: number;
}

// ---------- Nooaah Readiness type ----------

export interface NooaahReadinessCondition {
  key: string;
  label: string;
  current: number;
  target: number;
  unit: string;
  met: boolean;
}

export interface NooaahReadinessResponse {
  mode: string;
  all_met: boolean;
  conditions: NooaahReadinessCondition[];
  days_in_paper: number;
  recent_trades_count: number;
  recent_win_rate: number;
  recent_return: number;
}

// ---------- Nooaah Draft type ----------

export interface NooaahDraftResponse {
  draft: Record<string, unknown>;
  defaults: Record<string, unknown>;
  merged: Record<string, unknown>;
  step_completed: {
    step2_strategy: boolean;
    step3_position: boolean;
    step4_capital: boolean;
    step5_risk: boolean;
  };
}

// ---------- Nooaah Stop types ----------

export interface NooaahStopPosition {
  client_id: string;
  symbol: string;
  entry_price: number;
  entry_time: number;
  quantity: number;
  capital_used: number;
  best_bid: number;
  last_price: number;
  pnl_pct: number;
  pnl_abs: number;
  confidence: number;
}

export interface NooaahStopPreviewResponse {
  mode: string;
  open_positions: NooaahStopPosition[];
  count: number;
  total_pnl_abs: number;
  capital_in_use: number;
}

export interface NooaahStopResultResponse {
  action: string;
  mode: string;
  killed: boolean;
  open_positions: number;
  capital_available: number;
  capital_in_use: number;
}

// ---------- Nooaah Cycle Log ----------

export interface NooaahCycleLogResponse {
  timestamp: number;
  status: string;
  action: string;
  reason_fa: string;
  symbols_analyzed: string[];
  opened_symbol: string | null;
  opened_confidence: number | null;
  closed_count: number;
}

