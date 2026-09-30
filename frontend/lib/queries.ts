"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ProfitabilityRequest } from "./api";
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
