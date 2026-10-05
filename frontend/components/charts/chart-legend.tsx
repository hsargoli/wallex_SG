"use client";

import { cn } from "@/lib/utils";

export interface LegendData {
  time?: number;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  changePct?: number;
  // overlay indicators
  ema9?: number | null;
  ema21?: number | null;
  bbUpper?: number | null;
  bbMiddle?: number | null;
  bbLower?: number | null;
  // pane indicators
  rsi?: number | null;
  macd?: number | null;
  macdSignal?: number | null;
  macdHist?: number | null;
}

interface ChartLegendProps {
  data?: LegendData;
  showEMA?: boolean;
  showBB?: boolean;
  showRSI?: boolean;
  showMACD?: boolean;
}

function fmt(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined) return "—";
  if (Math.abs(v) >= 1_000_000) {
    return v.toLocaleString("en-US", { maximumFractionDigits: 0 });
  }
  return v.toLocaleString("en-US", { maximumFractionDigits: digits });
}

function fmtTime(t?: number): string {
  if (!t) return "—";
  const d = new Date(t * 1000);
  const date = d.toISOString().slice(0, 10);
  const time = d.toISOString().slice(11, 16);
  return `${date} ${time}`;
}

export function ChartLegend({
  data,
  showEMA = true,
  showBB = false,
  showRSI = true,
  showMACD = true,
}: ChartLegendProps) {
  if (!data) {
    return (
      <div className="rounded-lg border border-white/5 bg-card/50 px-3 py-2 text-xs text-muted-foreground">
        برای دیدن جزئیات، موس رو روی چارت حرکت بده
      </div>
    );
  }

  const changeColor =
    data.changePct === undefined
      ? "text-muted-foreground"
      : data.changePct >= 0
        ? "text-emerald-400"
        : "text-red-400";

  return (
    <div className="rounded-lg border border-white/5 bg-card/50 px-3 py-2 text-xs">
      {/* Row 1: time + OHLC + change */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 font-mono">
        <span className="text-muted-foreground">{fmtTime(data.time)}</span>
        <span>
          <span className="text-muted-foreground">O</span>{" "}
          <span className="font-bold">{fmt(data.open)}</span>
        </span>
        <span>
          <span className="text-muted-foreground">H</span>{" "}
          <span className="font-bold text-emerald-400">{fmt(data.high)}</span>
        </span>
        <span>
          <span className="text-muted-foreground">L</span>{" "}
          <span className="font-bold text-red-400">{fmt(data.low)}</span>
        </span>
        <span>
          <span className="text-muted-foreground">C</span>{" "}
          <span className="font-bold">{fmt(data.close)}</span>
        </span>
        {data.changePct !== undefined && (
          <span className={cn("font-bold", changeColor)}>
            {data.changePct >= 0 ? "+" : ""}
            {data.changePct.toFixed(2)}%
          </span>
        )}
      </div>

      {/* Row 2: overlays */}
      {(showEMA || showBB) && (
        <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-0.5 font-mono text-[11px]">
          {showEMA && (
            <>
              <span className="text-emerald-400">
                EMA9 <span className="font-bold">{fmt(data.ema9)}</span>
              </span>
              <span className="text-amber-400">
                EMA21 <span className="font-bold">{fmt(data.ema21)}</span>
              </span>
            </>
          )}
          {showBB && (
            <span className="text-purple-400">
              BB{" "}
              <span className="font-bold">
                {fmt(data.bbLower)} — {fmt(data.bbUpper)}
              </span>
            </span>
          )}
        </div>
      )}

      {/* Row 3: pane indicators */}
      {(showRSI || showMACD) && (
        <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-0.5 font-mono text-[11px]">
          {showRSI && (
            <span className="text-purple-400">
              RSI <span className="font-bold">{fmt(data.rsi, 1)}</span>
            </span>
          )}
          {showMACD && (
            <>
              <span className="text-emerald-400">
                MACD <span className="font-bold">{fmt(data.macd, 4)}</span>
              </span>
              <span className="text-amber-400">
                Signal <span className="font-bold">{fmt(data.macdSignal, 4)}</span>
              </span>
              {data.macdHist !== null && data.macdHist !== undefined && (
                <span
                  className={cn(
                    "font-bold",
                    data.macdHist >= 0 ? "text-emerald-400" : "text-red-400",
                  )}
                >
                  Hist {data.macdHist >= 0 ? "+" : ""}
                  {data.macdHist.toFixed(4)}
                </span>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
