"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ProfitabilityRequest, type PlaceOrderRequest, type BatchSignalItem } from "./api";
import { toast } from "sonner";

export function useBudget() {
  return useQuery({
    queryKey: ["budget"],
    queryFn: () => api.getBudget(),
    refetchInterval: 5000,
  });
}

export function useSetBudget() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (amount: number) => api.setBudget(amount),
    onSuccess: (data) => {
      qc.setQueryData(["budget"], data);
      toast.success("بودجه با موفقیت به‌روزرسانی شد");
    },
    onError: (err: Error) => {
      toast.error(`خطا: ${err.message}`);
    },
  });
}

export function useMarkets() {
  return useQuery({
    queryKey: ["markets"],
    queryFn: () => api.listMarkets(),
    staleTime: 30_000,
  });
}

export function useOrderBook(symbol: string | null) {
  return useQuery({
    queryKey: ["orderbook", symbol],
    queryFn: () => api.getOrderBook(symbol!),
    enabled: !!symbol,
    refetchInterval: 3000,
  });
}

export function useProfitability() {
  return useMutation({
    mutationFn: (payload: ProfitabilityRequest) =>
      api.evaluateProfitability(payload),
    onError: (err: Error) => {
      toast.error(`خطا در محاسبه: ${err.message}`);
    },
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => api.health(),
    refetchInterval: 10_000,
    retry: 1,
  });
}

export function useWallet() {
  return useQuery({
    queryKey: ["wallet"],
    queryFn: () => api.getWalletBalances(),
    refetchInterval: 10_000,
  });
}


export function usePortfolio() {
  return useQuery({
    queryKey: ["portfolio"],
    queryFn: () => api.getPortfolio(),
    refetchInterval: 15_000,
  });
}

export function useCandles(
  symbol: string | null,
  timeframe: import("./api").Timeframe,
  limit = 500,
) {
  return useQuery({
    queryKey: ["candles", symbol, timeframe, limit],
    queryFn: () => api.getCandles(symbol!, timeframe, limit),
    enabled: !!symbol,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}

export function useCandlesV2(
  symbol: string | null,
  timeframe: string,
  limit = 500,
) {
  return useQuery({
    queryKey: ["candles-v2", symbol, timeframe, limit],
    queryFn: () =>
      api.getCandlesV2(symbol!, timeframe as import("./api").Timeframe, limit),
    enabled: !!symbol,
    staleTime: 60_000,
  });
}

export function useFacts(symbol: string | null) {
  return useQuery({
    queryKey: ["facts", symbol],
    queryFn: () => api.getFacts(symbol!),
    enabled: !!symbol,
    staleTime: 5 * 60_000,  // 5 دقیقه cache
  });
}


export function useSignal(symbol: string | null, timeframe: string = "1h") {
  return useQuery({
    queryKey: ["signal", symbol, timeframe],
    queryFn: () => api.getSignal(symbol!, timeframe),
    enabled: !!symbol,
    refetchInterval: 60_000,
  });
}

export function useMultiTfSignals(symbol: string | null) {
  return useQuery({
    queryKey: ["signal-multi", symbol],
    queryFn: () => api.getMultiTfSignals(symbol!),
    enabled: !!symbol,
    refetchInterval: 120_000,
  });
}


export function useLevels(symbol: string | null, timeframe: string = "1h") {
  return useQuery({
    queryKey: ["levels", symbol, timeframe],
    queryFn: () => api.getLevels(symbol!, timeframe),
    enabled: !!symbol,
    refetchInterval: 120_000,
  });
}


export function useIndicators(symbol: string | null, timeframe: string = "1h", limit: number = 500) {
  return useQuery({
    queryKey: ["indicators", symbol, timeframe, limit],
    queryFn: () => api.getIndicators(symbol!, timeframe, limit),
    enabled: !!symbol,
    staleTime: 30_000,
  });
}


export function useScannerList(page: number, pageSize: number = 15, quote: string = "TMN") {
  return useQuery({
    queryKey: ["scanner-list", page, pageSize, quote],
    queryFn: () => api.getScannerList(page, pageSize, quote),
    staleTime: 5 * 60_000,
    placeholderData: (prev) => prev,
  });
}

export function useScanSymbols(symbols: string[], tf: string = "1h") {
  return useQuery({
    queryKey: ["scanner-scan", symbols.join(","), tf],
    queryFn: () => api.scanSymbols(symbols, tf),
    enabled: symbols.length > 0,
    staleTime: 60_000,
  });
}

export function usePaperV2Status() {
  return useQuery({
    queryKey: ["paper-v2-status"],
    queryFn: () => api.getPaperV2Status(),
    refetchInterval: 15_000,
  });
}

export function useStartPaperV2() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.startPaperV2(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["paper-v2-status"] });
      toast.success("ربات Paper Trading شروع شد");
    },
    onError: (err: Error) => toast.error(`خطا: ${err.message}`),
  });
}

export function useStopPaperV2() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.stopPaperV2(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["paper-v2-status"] });
      toast.success("ربات متوقف شد");
    },
  });
}

export function useResetPaperV2() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.resetPaperV2(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["paper-v2-status"] });
      toast.success("ریست شد");
    },
  });
}

// ==================== Bots ====================

export function useBots() {
  return useQuery({
    queryKey: ["bots"],
    queryFn: () => api.listBots(),
    refetchInterval: 30_000,
  });
}

export function useBot(slug: string) {
  return useQuery({
    queryKey: ["bot", slug],
    queryFn: () => api.getBot(slug),
    enabled: !!slug,
  });
}

export function useBotStatus(slug: string) {
  return useQuery({
    queryKey: ["bot-status", slug],
    queryFn: () => api.getBotStatus(slug),
    enabled: !!slug,
    refetchInterval: 15_000,
  });
}

export function useStartBot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => api.startBot(slug),
    onSuccess: (_, slug) => {
      qc.invalidateQueries({ queryKey: ["bot-status", slug] });
      qc.invalidateQueries({ queryKey: ["bots"] });
      toast.success("ربات شروع شد");
    },
    onError: (err: Error) => toast.error(`خطا: ${err.message}`),
  });
}

export function useStopBot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => api.stopBot(slug),
    onSuccess: (_, slug) => {
      qc.invalidateQueries({ queryKey: ["bot-status", slug] });
      qc.invalidateQueries({ queryKey: ["bots"] });
      toast.success("ربات متوقف شد");
    },
    onError: (err: Error) => toast.error(`خطا: ${err.message}`),
  });
}

export function useSetBotTimeframe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ slug, timeframe }: { slug: string; timeframe: string }) =>
      api.setBotTimeframe(slug, timeframe),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ["bot-status", variables.slug] });
      qc.invalidateQueries({ queryKey: ["bot", variables.slug] });
      toast.success("تایم‌فریم تغییر کرد");
    },
    onError: (err: Error) => toast.error(`خطا: ${err.message}`),
  });
}

export function usePaperV3Status() {
  return useQuery({
    queryKey: ["paper-v3-status"],
    queryFn: () => api.getPaperV3Status(),
    refetchInterval: 5_000,
  });
}

export function useLivePaperV3() {
  return useQuery({
    queryKey: ["paper-v3-live"],
    queryFn: () => api.getPaperV3Live(),
    refetchInterval: 5_000,
  });
}

export function useStartPaperV3() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: any) => api.startPaperV3(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["paper-v3-status"] });
      toast.success("Paper Trading v3 شروع شد");
    },
    onError: (err: Error) => toast.error(`خطا: ${err.message}`),
  });
}

export function useStopPaperV3() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.stopPaperV3(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["paper-v3-status"] });
      toast.success("متوقف شد");
    },
  });
}

export function useResetPaperV3() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.resetPaperV3(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["paper-v3-status"] });
      toast.success("ریست شد");
    },
  });
}

export function useSetBotSymbols() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ slug, symbols }: { slug: string; symbols: string[] }) =>
      api.setBotSymbols(slug, symbols),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ["bot-status", variables.slug] });
      qc.invalidateQueries({ queryKey: ["bot", variables.slug] });
      toast.success("نمادها تغییر کرد");
    },
    onError: (err: Error) => toast.error(`خطا: ${err.message}`),
  });
}

export function useResetBot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => api.resetBot(slug),
    onSuccess: (_, slug) => {
      qc.invalidateQueries({ queryKey: ["bot-status", slug] });
      qc.invalidateQueries({ queryKey: ["bots"] });
      toast.success("ربات ریست شد");
    },
    onError: (err: Error) => toast.error(`خطا: ${err.message}`),
  });
}

// ---------- Orders Hooks ----------

export function useOrders(symbol?: string, status?: string) {
  return useQuery({
    queryKey: ["orders", symbol ?? "all", status ?? "all"],
    queryFn: () => api.listOrders(symbol, status),
    refetchInterval: 10_000,
  });
}

export function usePlaceOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: PlaceOrderRequest) => api.placeOrder(payload),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["orders"] });
      toast.success(
        `سفارش ثبت شد: ${data.side} ${data.symbol} (${data.client_id})`,
      );
    },
    onError: (err: Error) => {
      const msg = err.message || "خطای نامشخص";
      // تشخیص خطاهای رایج
      if (msg.includes("403") || msg.includes("غیرفعال")) {
        toast.error("معامله واقعی غیرفعال است. با ادمین تماس بگیرید.");
      } else if (msg.includes("429") || msg.includes("محدودیت")) {
        toast.error("تعداد درخواست‌ها زیاد است. کمی صبر کنید.");
      } else if (msg.includes("موجودی")) {
        toast.error("موجودی کافی نیست.");
      } else {
        toast.error(`خطا در ثبت سفارش: ${msg}`);
      }
    },
  });
}

export function useCancelOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ clientId, symbol }: { clientId: string; symbol: string }) =>
      api.cancelOrder(clientId, symbol),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["orders"] });
      toast.success(`سفارش لغو شد: ${data.client_id}`);
    },
    onError: (err: Error) => {
      toast.error(`خطا در لغو: ${err.message}`);
    },
  });
}

export function useOpenOrders(symbol?: string) {
  return useQuery({
    queryKey: ["open-orders", symbol ?? "all"],
    queryFn: () => api.listOpenOrders(symbol),
    refetchInterval: 10_000,
  });
}

// ---------- Bot Budget Hooks ----------

export function useTotalBudget() {
  return useQuery({
    queryKey: ["total-budget"],
    queryFn: () => api.getTotalBudget(),
    refetchInterval: 15_000,
  });
}

export function useBotBudgets() {
  return useQuery({
    queryKey: ["bot-budgets"],
    queryFn: () => api.listBotBudgets(),
    refetchInterval: 15_000,
  });
}

export function useBotBudget(slug: string) {
  return useQuery({
    queryKey: ["bot-budget", slug],
    queryFn: () => api.getBotBudget(slug),
    enabled: !!slug,
  });
}

export function useSetBotBudget() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ slug, amount }: { slug: string; amount: number }) =>
      api.setBotBudget(slug, amount),
    onSuccess: (data, { slug }) => {
      qc.invalidateQueries({ queryKey: ["bot-budgets"] });
      qc.invalidateQueries({ queryKey: ["bot-budget", slug] });
      qc.invalidateQueries({ queryKey: ["total-budget"] });
      toast.success(`بودجه به ${data.allocated} TMN به‌روز شد`);
    },
    onError: (err: Error) => {
      toast.error(`خطا: ${err.message}`);
    },
  });
}

export function useMarket(symbol: string | null) {
  return useQuery({
    queryKey: ["market", symbol],
    queryFn: () => api.getMarket(symbol!),
    enabled: !!symbol,
    refetchInterval: 15_000,
  });
}

export function useBatchSignals(symbols: string[], tf: string = "1h") {
  return useQuery({
    queryKey: ["batch-signals", symbols.join(","), tf],
    queryFn: () =>
      api.getBatchSignals({ symbols, tf, limit: 200 }),
    enabled: symbols.length > 0,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}

// ============================================================
// All Signals — prefetch all, filter client-side
// ============================================================

const BATCH_SIZE = 20;
const CONCURRENT_BATCHES = 3;

/**
 * Fetch all signals for the given list of symbols in chunks.
 *
 * Designed for scenarios where you want to filter across ALL symbols
 * (not just the current page). Uses a single query key per timeframe
 * so it's cached across the whole app.
 */
export function useAllSignals(symbols: string[], tf: string = "1h") {
  return useQuery({
    queryKey: ["all-signals", tf, symbols.length],
    queryFn: async () => {
      if (symbols.length === 0) return { signals: [] };

      const chunks: string[][] = [];
      for (let i = 0; i < symbols.length; i += BATCH_SIZE) {
        chunks.push(symbols.slice(i, i + BATCH_SIZE));
      }

      // Run with concurrency limit
      const all: BatchSignalItem[] = [];
      for (let i = 0; i < chunks.length; i += CONCURRENT_BATCHES) {
        const batch = chunks.slice(i, i + CONCURRENT_BATCHES);
        const results = await Promise.all(
          batch.map((chunk) =>
            api.getBatchSignals({ symbols: chunk, tf, limit: 200 }),
          ),
        );
        for (const r of results) {
          all.push(...r.signals);
        }
      }

      return { signals: all };
    },
    enabled: symbols.length > 0,
    staleTime: 5 * 60_000, // 5 minutes
    gcTime: 10 * 60_000,
  });
}

/**
 * Progress-aware version: tracks how many batches have completed.
 * Use this for showing a progress bar during initial load.
 */
export function useAllSignalsWithProgress(
  symbols: string[],
  tf: string = "1h",
) {
  const [progress, setProgress] = useState({ loaded: 0, total: 0 });

  const query = useQuery({
    queryKey: ["all-signals-progress", tf, symbols.length],
    queryFn: async () => {
      if (symbols.length === 0) {
        setProgress({ loaded: 0, total: 0 });
        return { signals: [] };
      }

      const chunks: string[][] = [];
      for (let i = 0; i < symbols.length; i += BATCH_SIZE) {
        chunks.push(symbols.slice(i, i + BATCH_SIZE));
      }

      setProgress({ loaded: 0, total: chunks.length });

      const all: BatchSignalItem[] = [];
      let loaded = 0;

      for (let i = 0; i < chunks.length; i += CONCURRENT_BATCHES) {
        const batch = chunks.slice(i, i + CONCURRENT_BATCHES);
        const results = await Promise.all(
          batch.map((chunk) =>
            api.getBatchSignals({ symbols: chunk, tf, limit: 200 }),
          ),
        );
        for (const r of results) {
          all.push(...r.signals);
        }
        loaded += batch.length;
        setProgress({ loaded, total: chunks.length });
      }

      return { signals: all };
    },
    enabled: symbols.length > 0,
    staleTime: 5 * 60_000,
    gcTime: 10 * 60_000,
  });

  return { ...query, progress };
}


export function useCostBasis() {
  return useQuery({
    queryKey: ["cost-basis"],
    queryFn: () => api.getCostBasis(),
    refetchInterval: 60_000,
  });
}


export function useMarketOverview(symbol: string | null, tf: string = "1h") {
  return useQuery({
    queryKey: ["market-overview", symbol, tf],
    queryFn: () => api.getMarketOverview(symbol!, tf),
    enabled: !!symbol,
    staleTime: 5_000,
    refetchInterval: 15_000,
  });
}

export function useAnalysis(symbol: string | null, timeframe: string = "1h") {
  return useQuery({
    queryKey: ["analysis", symbol, timeframe],
    queryFn: () => api.getAnalysis(symbol!, timeframe),
    enabled: !!symbol,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}

