"use client";

import { ArrowLeftRight, TrendingUp, TrendingDown, Zap, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { MoneyFlow } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Props {
  data: MoneyFlow | null;
}

const COMBINED_STYLES: Record<
  MoneyFlow["combined"],
  { border: string; bg: string; text: string; icon: React.ComponentType<{ className?: string }> }
> = {
  confirmed_bullish: {
    border: "border-emerald-500/30",
    bg: "bg-emerald-500/[0.08]",
    text: "text-emerald-400",
    icon: CheckCircle2,
  },
  confirmed_bearish: {
    border: "border-red-500/30",
    bg: "bg-red-500/[0.08]",
    text: "text-red-400",
    icon: CheckCircle2,
  },
  divergence_resistance: {
    border: "border-amber-500/30",
    bg: "bg-amber-500/[0.08]",
    text: "text-amber-400",
    icon: AlertTriangle,
  },
  divergence_support: {
    border: "border-amber-500/30",
    bg: "bg-amber-500/[0.08]",
    text: "text-amber-400",
    icon: AlertTriangle,
  },
  neutral: {
    border: "border-zinc-500/30",
    bg: "bg-zinc-500/[0.06]",
    text: "text-zinc-400",
    icon: Zap,
  },
};

const PRESSURE_STYLES: Record<
  MoneyFlow["pressure"],
  { cls: string; barCls: string }
> = {
  strong_buy: {
    cls: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
    barCls: "bg-emerald-500",
  },
  buy: {
    cls: "border-emerald-500/20 bg-emerald-500/[0.06] text-emerald-400",
    barCls: "bg-emerald-500/70",
  },
  balanced: {
    cls: "border-zinc-500/20 bg-zinc-500/[0.06] text-zinc-400",
    barCls: "bg-zinc-500/70",
  },
  sell: {
    cls: "border-red-500/20 bg-red-500/[0.06] text-red-400",
    barCls: "bg-red-500/70",
  },
  strong_sell: {
    cls: "border-red-500/30 bg-red-500/10 text-red-400",
    barCls: "bg-red-500",
  },
};

function fmtVol(v: string | number): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(2)}K`;
  if (n >= 1) return n.toFixed(4);
  return n.toFixed(6);
}

export function MoneyFlowCard({ data }: Props) {
  if (!data) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <ArrowLeftRight className="h-4 w-4 text-purple-400" />
            جریان پول (۳۰ دقیقه اخیر)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">داده‌ای در دسترس نیست</p>
        </CardContent>
      </Card>
    );
  }

  const style = PRESSURE_STYLES[data.pressure];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <ArrowLeftRight className="h-4 w-4 text-purple-400" />
          جریان پول (۳۰ دقیقه اخیر)
        </CardTitle>
        <span
          className={cn(
            "rounded-md border px-2 py-0.5 text-[11px] font-bold",
            style.cls,
          )}
        >
          {data.pressure_fa}
        </span>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* خط تغییر قیمت در همین بازه */}
        {data.price_change_pct !== null && (
          <div className="flex items-center justify-between rounded-lg border border-border/50 bg-background/40 px-3 py-2">
            <span className="text-[11px] text-muted-foreground">
              تغییر قیمت در این بازه
            </span>
            <span
              className={cn(
                "flex items-center gap-1 font-mono text-sm font-bold",
                data.price_change_pct > 0
                  ? "text-emerald-400"
                  : data.price_change_pct < 0
                    ? "text-red-400"
                    : "text-zinc-400",
              )}
            >
              {data.price_change_pct > 0 ? (
                <TrendingUp className="h-3.5 w-3.5" />
              ) : data.price_change_pct < 0 ? (
                <TrendingDown className="h-3.5 w-3.5" />
              ) : null}
              {data.price_change_pct >= 0 ? "+" : ""}
              {data.price_change_pct.toFixed(3)}%
            </span>
          </div>
        )}

        {/* نوار نسبت خرید/فروش */}
        <div>
          <div className="mb-2 flex items-center justify-between text-xs">
            <span className="flex items-center gap-1 text-emerald-400">
              <TrendingUp className="h-3 w-3" />
              خریداران {data.buy_pct}٪
            </span>
            <span className="flex items-center gap-1 text-red-400">
              فروشندگان {data.sell_pct}٪
              <TrendingDown className="h-3 w-3" />
            </span>
          </div>
          <div className="flex h-2 overflow-hidden rounded-full bg-red-500/20">
            <div
              className="bg-emerald-500 transition-all"
              style={{ width: `${data.buy_pct}%` }}
            />
          </div>
        </div>

        {/* جزئیات */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg border border-emerald-500/15 bg-emerald-500/[0.03] p-2.5">
            <p className="text-[10px] text-muted-foreground">
              حجم خرید ({data.buy_count} معامله)
            </p>
            <p className="mt-0.5 font-mono text-sm font-bold text-emerald-400">
              {fmtVol(data.buy_volume)}
            </p>
          </div>
          <div className="rounded-lg border border-red-500/15 bg-red-500/[0.03] p-2.5">
            <p className="text-[10px] text-muted-foreground">
              حجم فروش ({data.sell_count} معامله)
            </p>
            <p className="mt-0.5 font-mono text-sm font-bold text-red-400">
              {fmtVol(data.sell_volume)}
            </p>
          </div>
        </div>

        {/* تفسیر ترکیبی (واگرایی) */}
        {(() => {
          const style = COMBINED_STYLES[data.combined];
          const Icon = style.icon;
          return (
            <div
              className={cn(
                "flex items-start gap-2 rounded-lg border p-2.5 text-[11px]",
                style.border,
                style.bg,
              )}
            >
              <Icon className={cn("mt-0.5 h-3.5 w-3.5 shrink-0", style.text)} />
              <div className="min-w-0">
                <p className={cn("font-bold", style.text)}>
                  {data.combined_fa}
                </p>
                <p className="mt-0.5 text-muted-foreground">
                  بر اساس {data.total_trades} معامله‌ی آخر والکس (~۳۰ دقیقه)
                </p>
              </div>
            </div>
          );
        })()}

        {/* یادداشت شفافیت */}
        <p className="rounded-md border border-dashed border-border/40 bg-background/30 px-2.5 py-2 text-[10px] leading-relaxed text-muted-foreground">
          ℹ️ این تحلیل <span className="font-bold text-foreground">فقط بر اساس حجم خرید و فروش</span> است
          و با سیگنال اصلی (RSI/EMA/MACD در تب تحلیل) ممکن است تفاوت داشته باشد.
          برای تصمیم نهایی، هر دو را با هم ببینید.
        </p>
      </CardContent>
    </Card>
  );
}
