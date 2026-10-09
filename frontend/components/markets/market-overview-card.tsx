"use client";

import { TrendingUp, TrendingDown, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarketOverview } from "@/lib/queries";
import { cn } from "@/lib/utils";

interface MarketOverviewCardProps {
  symbol: string;
  timeframe?: string;
}

const SIGNAL_LABEL: Record<string, { label: string; cls: string }> = {
  buy: {
    label: "خرید",
    cls: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  },
  sell: {
    label: "فروش",
    cls: "border-red-500/30 bg-red-500/10 text-red-400",
  },
  hold: {
    label: "بی‌طرف",
    cls: "border-zinc-500/30 bg-zinc-500/10 text-zinc-400",
  },
};

const STRENGTH_LABEL: Record<string, string> = {
  strong: "قوی",
  medium: "متوسط",
  weak: "ضعیف",
};

const PERIODS: Array<{ key: keyof Changes; label: string }> = [
  { key: "h1", label: "۱ ساعت" },
  { key: "h24", label: "۲۴ ساعت" },
  { key: "d7", label: "۷ روز" },
  { key: "m1", label: "۱ ماه" },
  { key: "m3", label: "۳ ماه" },
  { key: "y1", label: "۱ سال" },
];

type Changes = {
  h1: number | null;
  h24: number | null;
  d7: number | null;
  m1: number | null;
  m3: number | null;
  y1: number | null;
};

function fmtPct(v: number | null): string {
  if (v === null) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
}

function pctTone(v: number | null): string {
  if (v === null) return "text-muted-foreground";
  if (v > 0) return "text-emerald-400";
  if (v < 0) return "text-red-400";
  return "text-foreground";
}

export function MarketOverviewCard({
  symbol,
  timeframe = "1h",
}: MarketOverviewCardProps) {
  const q = useMarketOverview(symbol, timeframe);

  if (q.isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Zap className="h-4 w-4 text-emerald-400" />
            نگاه کلی
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!q.data) return null;

  const { changes, signal } = q.data;
  const sig = SIGNAL_LABEL[signal.type] ?? SIGNAL_LABEL.hold;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Zap className="h-4 w-4 text-emerald-400" />
          نگاه کلی
        </CardTitle>
        <Badge variant="outline" className={cn("border text-[11px]", sig.cls)}>
          {sig.label} ({STRENGTH_LABEL[signal.strength] ?? signal.strength}) —{" "}
          {signal.confidence}٪
        </Badge>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* ۶ بازه‌ی تغییر */}
        <div className="grid grid-cols-3 gap-2 md:grid-cols-6">
          {PERIODS.map(({ key, label }) => {
            const v = changes[key as keyof Changes];
            return (
              <div
                key={key}
                className="rounded-lg border border-border/50 bg-background/40 px-2 py-2 text-center"
              >
                <p className="text-[10px] text-muted-foreground">{label}</p>
                <p
                  className={cn(
                    "mt-1 flex items-center justify-center gap-0.5 font-mono text-sm font-bold",
                    pctTone(v),
                  )}
                >
                  {v !== null && v > 0 && <TrendingUp className="h-3 w-3" />}
                  {v !== null && v < 0 && <TrendingDown className="h-3 w-3" />}
                  {fmtPct(v)}
                </p>
              </div>
            );
          })}
        </div>

        {/* چرا؟ + SL/TP */}
        <div className="flex flex-wrap items-start justify-between gap-3 border-t border-border/40 pt-3">
          <div className="min-w-0 flex-1">
            <p className="text-[10px] text-muted-foreground">چرا این سیگنال؟</p>
            <p className="mt-0.5 truncate text-xs text-foreground">
              {signal.reasons?.slice(0, 2).join(" · ") || "—"}
            </p>
          </div>

          <div className="flex items-center gap-4 font-mono text-xs">
            {signal.stop_loss && (
              <div className="text-right">
                <p className="text-[10px] text-muted-foreground">حد ضرر</p>
                <p className="text-red-400">
                  {Number(signal.stop_loss).toLocaleString("en-US")}
                </p>
              </div>
            )}
            {signal.take_profit && (
              <div className="text-right">
                <p className="text-[10px] text-muted-foreground">حد سود</p>
                <p className="text-emerald-400">
                  {Number(signal.take_profit).toLocaleString("en-US")}
                </p>
              </div>
            )}
            {signal.risk_reward && (
              <div className="text-right">
                <p className="text-[10px] text-muted-foreground">R/R</p>
                <p className="text-foreground">
                  {Number(signal.risk_reward).toFixed(2)}
                </p>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
