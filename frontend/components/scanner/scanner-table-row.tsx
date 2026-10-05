"use client";

import Link from "next/link";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatPrice } from "@/lib/format";
import { Sparkline } from "./sparkline";

const SIGNAL_BADGE = {
  buy: { label: "خرید", cls: "border-emerald-500/30 bg-emerald-500/15 text-emerald-400" },
  sell: { label: "فروش", cls: "border-red-500/30 bg-red-500/15 text-red-400" },
  hold: { label: "بی‌طرف", cls: "border-zinc-500/30 bg-zinc-500/15 text-zinc-400" },
} as const;

const STRENGTH_LABEL: Record<string, string> = {
  strong: "قوی",
  medium: "متوسط",
  weak: "ضعیف",
};

const DIRECTION_ICON = {
  bullish: TrendingUp,
  bearish: TrendingDown,
  neutral: Minus,
} as const;

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
  sparkline: number[];
}

interface ScannerTableRowProps {
  item: ScanItem;
}

export function ScannerTableRow({ item }: ScannerTableRowProps) {
  const change24 = item.change_24h ? Number(item.change_24h) : 0;
  const isUp24 = change24 >= 0;
  const isTMN = item.symbol.endsWith("TMN");

  const sig = SIGNAL_BADGE[item.signal as keyof typeof SIGNAL_BADGE] || SIGNAL_BADGE.hold;
  const DirIcon = DIRECTION_ICON[item.direction as keyof typeof DIRECTION_ICON] || Minus;

  const atrPct = item.atr_pct ? Number(item.atr_pct) : null;
  const atrTone =
    atrPct === null
      ? "text-muted-foreground"
      : atrPct < 0.5
        ? "text-zinc-400"
        : atrPct < 2
          ? "text-emerald-400"
          : "text-amber-400";

  const rsi = item.rsi_14 ? Number(item.rsi_14) : null;
  const rsiTone =
    rsi === null
      ? "text-muted-foreground"
      : rsi >= 70
        ? "text-red-400"
        : rsi <= 30
          ? "text-emerald-400"
          : "text-foreground";

  return (
    <Link
      href={`/markets/${item.symbol}`}
      className="grid grid-cols-[minmax(140px,1.4fr)_minmax(70px,0.7fr)_minmax(80px,0.7fr)_minmax(90px,0.9fr)_minmax(70px,0.7fr)_minmax(70px,0.7fr)_minmax(70px,0.7fr)_minmax(80px,0.8fr)_80px] items-center gap-3 border-b border-white/5 px-4 py-3 text-sm transition hover:bg-emerald-500/[0.03]"
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
      <div className={cn("font-mono text-xs", isUp24 ? "text-emerald-400" : "text-red-400")}>
        {item.change_24h ? `${isUp24 ? "+" : ""}${change24.toFixed(2)}%` : "—"}
      </div>

      {/* Signal */}
      <div>
        <Badge variant="outline" className={cn("text-[10px]", sig.cls)}>
          {sig.label}
        </Badge>
      </div>

      {/* Strength + pattern */}
      <div className="min-w-0 text-xs">
        <p className="truncate text-foreground">{STRENGTH_LABEL[item.strength] || item.strength}</p>
        <p className="truncate text-[10px] text-muted-foreground">{item.pattern}</p>
      </div>

      {/* RSI */}
      <div className={cn("font-mono text-xs", rsiTone)}>
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

      {/* Trend score + direction */}
      <div className="flex items-center gap-1.5">
        <DirIcon className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        <span className="font-mono text-xs font-bold">{item.trend_score}</span>
      </div>

      {/* Sparkline */}
      <div className="flex justify-end">
        <Sparkline data={item.sparkline} />
      </div>
    </Link>
  );
}
