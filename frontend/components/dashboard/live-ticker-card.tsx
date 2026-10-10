"use client";

import { Radio } from "lucide-react";
import { useLiveTicker } from "@/lib/useLiveTicker";

function fmtChange(n: number): string {
  const sign = n >= 0 ? "+" : "";
  return `${sign}${n.toFixed(2)}%`;
}

export function LiveTickerCard({ symbol = "BTCTMN" }: { symbol?: string }) {
  const { price, change24h, lastUpdate, connected, stale } = useLiveTicker(symbol);

  const dot = !connected ? "bg-red-500" : stale ? "bg-amber-400" : "bg-emerald-500";
  const label = !connected ? "قطع" : stale ? "کهنه" : "زنده";
  const secondsAgo = lastUpdate ? Math.floor((Date.now() - lastUpdate) / 1000) : null;

  return (
    <div className="rounded-2xl border border-border/50 bg-card p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radio className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">{symbol}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${dot}`} />
          <span className="text-xs text-muted-foreground">{label}</span>
        </div>
      </div>
      <div className="mt-3 flex items-end justify-between">
        <div className="text-2xl font-bold tabular-nums">{price || "—"}</div>
        <div
          className={`text-sm font-medium tabular-nums ${
            change24h >= 0 ? "text-emerald-500" : "text-red-500"
          }`}
        >
          {fmtChange(change24h)}
        </div>
      </div>
      {secondsAgo !== null && (
        <div className="mt-1 text-xs text-muted-foreground">
          آخرین آپدیت: {secondsAgo} ثانیه پیش
        </div>
      )}
    </div>
  );
}
