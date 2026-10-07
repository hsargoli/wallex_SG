"use client";

import { useQuery } from "@tanstack/react-query";
import { getTradingMode } from "@/lib/api";

export function useLiveMode() {
  const q = useQuery({
    queryKey: ["trading-mode"],
    queryFn: getTradingMode,
    refetchInterval: 30_000,
    retry: 1,
  });
  return {
    liveOn: q.data?.live_enabled === true,
    known: !!q.data,
    loading: q.isLoading,
  };
}
