import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { getUserToken } from "@/lib/auth";

export interface LiveBotStatus {
  bot_status: string;
  signal_direction: string | null;
  signal_expires_at: string | null;
  signal_note: string | null;
  positions_count: number;
  trades_today: number;
  daily_volume_tmn: number;
  capital_tmn: number;
  waiting_liquidity_since: string | null;
  idle: boolean;
  is_killed: boolean;
  kill_reason: string | null;
  last_trade_at: string | null;
}

export function useLiveBotStatus() {
  return useQuery({
    queryKey: ["live-bot-status"],
    queryFn: () => api.getLiveBotStatus() as Promise<LiveBotStatus>,
    enabled: !!getUserToken(),
    refetchInterval: 5000,
    staleTime: 0,
    refetchOnWindowFocus: false,
    retry: 1,
  });
}

export function useSetLiveBotSignal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { direction: string; ttl_days: number; note?: string }) =>
      api.setLiveBotSignal(body) as Promise<LiveBotStatus>,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["live-bot-status"] }),
  });
}

export function useKillLiveBot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reason: string) =>
      api.killLiveBot({ reason }) as Promise<LiveBotStatus>,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["live-bot-status"] }),
  });
}

export function useResumeLiveBot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reason: string) =>
      api.resumeLiveBot({ reason }) as Promise<LiveBotStatus>,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["live-bot-status"] }),
  });
}
