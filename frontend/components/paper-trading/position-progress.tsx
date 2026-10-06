"use client";

interface Props {
  entry: number;
  current: number;
  tp: number;
  sl: number;
}

export function PositionProgress({ entry, current, tp, sl }: Props) {
  const range = tp - sl;
  if (range <= 0) return null;

  const pos = Math.max(0, Math.min(100, ((current - sl) / range) * 100));
  const entryPos = Math.max(0, Math.min(100, ((entry - sl) / range) * 100));

  const isProfit = current >= entry;
  const color = isProfit ? "emerald" : "red";
  const pnlPct = ((current / entry - 1) * 100).toFixed(2);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-[10px]">
        <span className="font-mono text-red-400">SL {formatNum(sl)}</span>
        <span className={`font-mono font-bold text-${color}-400`}>
          {isProfit ? "+" : ""}
          {pnlPct}%
        </span>
        <span className="font-mono text-emerald-400">TP {formatNum(tp)}</span>
      </div>

      <div className="relative h-2 overflow-hidden rounded-full bg-zinc-800">
        <div
          className="absolute left-0 top-0 h-full bg-gradient-to-r from-red-500/40 to-red-500/10"
          style={{ width: `${entryPos}%` }}
        />
        <div
          className="absolute right-0 top-0 h-full bg-gradient-to-l from-emerald-500/40 to-emerald-500/10"
          style={{ width: `${100 - entryPos}%` }}
        />
        <div
          className="absolute top-0 h-full w-0.5 bg-amber-400"
          style={{ left: `${entryPos}%` }}
        />
        <div
          className={`absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-${color}-500 shadow-lg shadow-${color}-500/50 transition-all duration-500`}
          style={{ left: `${pos}%` }}
        />
      </div>

      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
        <span>ورود {formatNum(entry)}</span>
        <span>فعلی {formatNum(current)}</span>
      </div>
    </div>
  );
}

function formatNum(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(3) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(2) + "K";
  return n.toFixed(4);
}
