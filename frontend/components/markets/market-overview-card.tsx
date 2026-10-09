"use client";

import { useState } from "react";
import { TrendingUp, TrendingDown, Zap, ArrowDown, BookOpen, ChevronDown } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarketOverview } from "@/lib/queries";
import { cn } from "@/lib/utils";
import { InfoTip } from "@/components/ui/info-tip";

interface MarketOverviewCardProps {
  symbol: string;
  timeframe?: string;
  /** اگه compact باشه، فقط ۴ بازه‌ی اول (1h/24h/7d/1m) */
  compact?: boolean;
  /** اگه beginner باشه، سرفصل‌ها ساده‌تر */
  beginner?: boolean;
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
  compact = false,
  beginner = false,
}: MarketOverviewCardProps) {
  const q = useMarketOverview(symbol, timeframe);
  const [showReasons, setShowReasons] = useState(false);

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
          <InfoTip text="خلاصه‌ی تغییر قیمت در ۶ بازه‌ی زمانی مختلف + سیگنال خرید/فروش + سطوح حد ضرر و حد سود." />
        </CardTitle>
        <Badge variant="outline" className={cn("border text-[11px]", sig.cls)}>
          {sig.label} ({STRENGTH_LABEL[signal.strength] ?? signal.strength}) —{" "}
          {signal.confidence}٪
        </Badge>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* ۶ بازه‌ی تغییر */}
        <div className={cn(
          "grid gap-2",
          compact ? "grid-cols-2 md:grid-cols-4" : "grid-cols-3 md:grid-cols-6",
        )}>
          {(compact ? PERIODS.slice(0, 4) : PERIODS).map(({ key, label }) => {
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

        {/* دکمه بازشو توضیحات */}
        <button
          type="button"
          onClick={() => setShowReasons((v) => !v)}
          className={cn(
            "flex w-full items-center justify-center gap-1.5 rounded-md border border-dashed py-2 text-[11px] transition-colors",
            showReasons
              ? "border-emerald-500/40 bg-emerald-500/[0.05] text-emerald-400"
              : "border-border/40 text-muted-foreground hover:border-emerald-500/30 hover:bg-emerald-500/[0.03] hover:text-emerald-400",
          )}
        >
          <BookOpen className="h-3.5 w-3.5" />
          {showReasons ? "بستن جزئیات سیگنال" : "جزئیات کامل سیگنال"}
          <ChevronDown
            className={cn(
              "h-3.5 w-3.5 transition-transform",
              showReasons && "rotate-180",
            )}
          />
        </button>

        {/* پنل جزئیات */}
        {showReasons && (
          <div className="space-y-3 rounded-lg border border-border/40 bg-background/40 p-3.5">
            {/* دلایل کامل */}
            <div>
              <p className="mb-2 text-[11px] font-bold text-muted-foreground">
                📋 دلایل کامل سیگنال
              </p>
              <ul className="space-y-1.5">
                {signal.reasons && signal.reasons.length > 0 ? (
                  signal.reasons.map((r, i) => (
                    <li key={i} className="flex items-start gap-2 text-[12px] leading-relaxed">
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                      <span>{r}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-[11px] text-muted-foreground">
                    دلیلی ثبت نشده
                  </li>
                )}
              </ul>
            </div>

            {/* امتیازها */}
            <div className="grid grid-cols-2 gap-2 border-t border-border/30 pt-3">
              <div className="rounded-md border border-emerald-500/20 bg-emerald-500/[0.04] p-2">
                <p className="text-[10px] text-muted-foreground">امتیاز خرید</p>
                <p className="mt-0.5 font-mono text-lg font-bold text-emerald-400">
                  {signal.buy_score}
                </p>
              </div>
              <div className="rounded-md border border-red-500/20 bg-red-500/[0.04] p-2">
                <p className="text-[10px] text-muted-foreground">امتیاز فروش</p>
                <p className="mt-0.5 font-mono text-lg font-bold text-red-400">
                  {signal.sell_score}
                </p>
              </div>
            </div>

            {/* سطوح کامل */}
            <div className="grid grid-cols-3 gap-2 border-t border-border/30 pt-3 text-center">
              {signal.stop_loss && (
                <div>
                  <p className="text-[10px] text-muted-foreground">حد ضرر</p>
                  <p className="mt-0.5 font-mono text-xs font-bold text-red-400">
                    {Number(signal.stop_loss).toLocaleString("en-US")}
                  </p>
                </div>
              )}
              {signal.take_profit && (
                <div>
                  <p className="text-[10px] text-muted-foreground">حد سود</p>
                  <p className="mt-0.5 font-mono text-xs font-bold text-emerald-400">
                    {Number(signal.take_profit).toLocaleString("en-US")}
                  </p>
                </div>
              )}
              {signal.risk_reward && (
                <div>
                  <p className="text-[10px] text-muted-foreground">R/R</p>
                  <p className="mt-0.5 font-mono text-xs font-bold">
                    {Number(signal.risk_reward).toFixed(2)}
                  </p>
                </div>
              )}
            </div>

            {/* توضیح کوتاه */}
            <p className="border-t border-border/30 pt-3 text-[11px] leading-relaxed text-muted-foreground">
              💡 سیگنال بر اساس ۶ قانون تکنیکال (RSI، MACD، EMA، باند بولینگر، حجم،
              روند) محاسبه شده. امتیازها مجموع وزن قوانین فعاله. برای تحلیل عمیق‌تر،
              به صفحه‌ی «تحلیل حرفه‌ای» برو.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
