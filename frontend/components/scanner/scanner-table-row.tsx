"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatPrice } from "@/lib/format";
import { Sparkline } from "./sparkline";

export interface ScanItem {
  symbol: string;
  current_price: string;
  trend_score: number;
  direction: string;
  strength: string;
  pattern: string;
  volatility_pct: string;
  change_24h: string | null;
  signal: string;
  risk_reward: string | null;
  rsi_14: string | null;
  atr_pct: string | null;
  ema_9: string | null;
  ema_21: string | null;
  ema_diff_pct: string | null;
  macd_hist: string | null;
  bb_pct: string | null;
  sparkline: number[];
}

interface ScannerTableRowProps {
  item: ScanItem;
}

/** رنگ سلول بر اساس مقدار عددی */
function tone(v: number | null, pos: number, neg: number): string {
  if (v === null) return "text-muted-foreground";
  if (v >= pos) return "text-emerald-400";
  if (v <= neg) return "text-red-400";
  return "text-foreground";
}

export function ScannerTableRow({ item }: ScannerTableRowProps) {
  const change24 = item.change_24h ? Number(item.change_24h) : null;
  const isTMN = item.symbol.endsWith("TMN");

  // EMA
  const emaDiff = item.ema_diff_pct ? Number(item.ema_diff_pct) : null;

  // MACD hist
  const macdHist = item.macd_hist ? Number(item.macd_hist) : null;
  const macdSig = macdHist === null ? "—" : macdHist >= 0 ? "↑" : "↓";

  // RSI
  const rsi = item.rsi_14 ? Number(item.rsi_14) : null;

  // ATR
  const atrPct = item.atr_pct ? Number(item.atr_pct) : null;
  const atrTone =
    atrPct === null
      ? "text-muted-foreground"
      : atrPct < 0.5
        ? "text-zinc-400"
        : atrPct < 2
          ? "text-emerald-400"
          : "text-amber-400";

  // BB%
  const bbPct = item.bb_pct ? Number(item.bb_pct) : null;
  const bbTone =
    bbPct === null
      ? "text-muted-foreground"
      : bbPct < 20
        ? "text-emerald-400"
        : bbPct > 80
          ? "text-red-400"
          : "text-foreground";

  return (
    <Link
      href={`/markets/${item.symbol}`}
      className="grid grid-cols-[minmax(140px,1.4fr)_minmax(70px,0.7fr)_minmax(85px,0.8fr)_minmax(80px,0.8fr)_minmax(65px,0.65fr)_minmax(65px,0.65fr)_minmax(70px,0.7fr)_minmax(70px,0.7fr)_80px] items-center gap-3 border-b border-white/5 px-4 py-3 text-sm transition hover:bg-emerald-500/[0.03]"
    >
      {/* Symbol + price */}
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <p className="font-mono font-bold">{item.symbol}</p>
          {isTMN && (
            <Badge variant="outline" className="text-[9px] border-emerald-500/20 bg-emerald-500/10 text-emerald-400">
              TMN
            </Badge>
          )}
        </div>
        <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
          {formatPrice(item.current_price)}
        </p>
      </div>

      {/* Change 24h */}
      <div className={cn("font-mono text-xs", change24 === null ? "text-muted-foreground" : change24 >= 0 ? "text-emerald-400" : "text-red-400")}>
        {change24 === null ? "—" : `${change24 >= 0 ? "+" : ""}${change24.toFixed(2)}%`}
      </div>

      {/* EMA 9/21 diff */}
      <div className={cn("font-mono text-xs", tone(emaDiff, 0.1, -0.1))}>
        {emaDiff === null ? "—" : `${emaDiff >= 0 ? "+" : ""}${emaDiff.toFixed(2)}%`}
      </div>

      {/* MACD hist */}
      <div className={cn("font-mono text-xs", macdHist === null ? "text-muted-foreground" : macdHist >= 0 ? "text-emerald-400" : "text-red-400")}>
        {macdHist === null ? "—" : `${macdSig} ${Math.abs(macdHist) >= 1 ? macdHist.toFixed(2) : macdHist.toFixed(4)}`}
      </div>

      {/* RSI */}
      <div className={cn("font-mono text-xs", rsi === null ? "text-muted-foreground" : rsi >= 70 ? "text-red-400" : rsi <= 30 ? "text-emerald-400" : "text-foreground")}>
        {rsi !== null ? rsi.toFixed(1) : "—"}
      </div>

      {/* R/R */}
      <div className="font-mono text-xs">
        {item.risk_reward ? Number(item.risk_reward).toFixed(2) : "—"}
      </div>

      {/* ATR% */}
      <div className={cn("font-mono text-xs", atrTone)}>
        {atrPct !== null ? `${atrPct.toFixed(2)}%` : "—"}
      </div>

      {/* BB% */}
      <div className={cn("font-mono text-xs", bbTone)}>
        {bbPct !== null ? `${bbPct.toFixed(0)}%` : "—"}
      </div>

      {/* Sparkline */}
      <div className="flex justify-end">
        <Sparkline data={item.sparkline} />
      </div>
    </Link>
  );
}
