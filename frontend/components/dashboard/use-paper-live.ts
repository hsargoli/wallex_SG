"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export type PaperLive = {
  running: boolean;
  equity: number | null;
  pnl: number | null;
  pnlPct: number | null;
  openCount: number;
  trades: number | null;
  winRate: number | null;
  idle: boolean;
};

const n = (v: unknown): number | null =>
  typeof v === "number" && Number.isFinite(v) ? v : null;

function normalize(raw: unknown): PaperLive {
  const r = (raw ?? {}) as Record<string, unknown>;
  const s = (r.state && typeof r.state === "object" ? r.state : r) as Record<string, unknown>;
  const op = s.open_positions;
  const openCount = Array.isArray(op)
    ? op.length
    : op && typeof op === "object"
      ? Object.keys(op).length
      : (n(op) ?? 0);
  const running = s.is_running === true;
  const pnlPct = n(s.total_pnl_pct);
  const trades = n(s.total_trades);
  return {
    running,
    equity: n(s.equity),
    pnl: n(s.total_pnl),
    pnlPct,
    openCount,
    trades,
    winRate: n(s.win_rate),
    idle: !running && (pnlPct ?? 0) === 0 && openCount === 0 && (trades ?? 0) === 0,
  };
}

export function usePaperLive() {
  return useQuery({
    queryKey: ["dash-paper-live-v2"],
    queryFn: async () => normalize(await api.getPaperV3Live()),
    refetchInterval: 10_000,
    retry: 1,
  });
}
