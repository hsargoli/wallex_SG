"use client";

import { cn } from "@/lib/utils";

const TIMEFRAMES = ["15m", "1h", "4h", "1D"] as const;
export type Timeframe = (typeof TIMEFRAMES)[number];

interface TimeframeTabsProps {
  value: Timeframe;
  onChange: (tf: Timeframe) => void;
}

export function TimeframeTabs({ value, onChange }: TimeframeTabsProps) {
  return (
    <div className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-background/50 p-1">
      {TIMEFRAMES.map((tf) => (
        <button
          key={tf}
          onClick={() => onChange(tf)}
          className={cn(
            "rounded px-3 py-1.5 font-mono text-xs font-medium transition",
            value === tf
              ? "bg-emerald-500/20 text-emerald-400"
              : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
          )}
        >
          {tf}
        </button>
      ))}
    </div>
  );
}
