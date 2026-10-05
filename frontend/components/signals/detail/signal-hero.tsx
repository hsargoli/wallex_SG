"use client";

import Link from "next/link";
import { ArrowUpRight, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { type SignalResponse } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { InfoTip } from "@/components/ui/info-tip";
import { cn } from "@/lib/utils";

interface SignalHeroProps {
  symbol: string;
  timeframe: string;
  signal?: SignalResponse;
  loading?: boolean;
}

const SIGNAL_CONFIG = {
  buy: {
    label: "خرید",
    icon: TrendingUp,
    color: "text-emerald-400",
    bg: "border-emerald-500/30 bg-emerald-500/10",
  },
  sell: {
    label: "فروش",
    icon: TrendingDown,
    color: "text-red-400",
    bg: "border-red-500/30 bg-red-500/10",
  },
  hold: {
    label: "بی‌طرف",
    icon: Minus,
    color: "text-zinc-400",
    bg: "border-zinc-500/30 bg-zinc-500/10",
  },
} as const;

const STRENGTH_LABEL: Record<string, string> = {
  strong: "قوی",
  medium: "متوسط",
  weak: "ضعیف",
};

export function SignalHero({
  symbol,
  timeframe,
  signal,
  loading,
}: SignalHeroProps) {
  if (loading) {
    return (
      <div className="rounded-xl border border-white/10 bg-card p-5">
        <div className="h-20 animate-pulse rounded bg-white/5" />
      </div>
    );
  }

  const sig = signal
    ? SIGNAL_CONFIG[signal.signal as keyof typeof SIGNAL_CONFIG] ||
      SIGNAL_CONFIG.hold
    : null;
  const Icon = sig?.icon || Minus;

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-white/10 bg-card p-5">
      {/* Left: Symbol + Price */}
      <div className="flex items-center gap-4">
        <Link
          href={`/markets/${symbol}/chart`}
          className="group flex items-center gap-3"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/15 font-mono text-sm font-bold text-emerald-400">
            {symbol.slice(0, 3)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <p className="font-mono text-lg font-bold">{symbol}</p>
              <ArrowUpRight className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
            </div>
            <p className="font-mono text-sm text-muted-foreground">
              {signal ? formatPrice(signal.current_price) : "—"}
            </p>
          </div>
        </Link>
      </div>

      {/* Right: Signal + Strength + TF */}
      {signal && sig && (
        <div className="flex flex-wrap items-center gap-3">
          <span
            title={
              signal.signal === "buy"
                ? "سیگنال خرید: اندیکاتورها احتمال افزایش قیمت رو می‌دن"
                : signal.signal === "sell"
                  ? "سیگنال فروش: اندیکاتورها احتمال کاهش قیمت رو می‌دن"
                  : "بی‌طرف: شرایط بازار برای معامله واضح نیست"
            }
            className="cursor-help"
          >
            <Badge
              variant="outline"
              className={cn("gap-1.5 py-1.5 text-sm", sig.bg, sig.color)}
            >
              <Icon className="h-4 w-4" />
              {sig.label}
            </Badge>
          </span>
          <span
            title={
              signal.strength === "strong"
                ? "قوی: چند اندیکاتور مستقل هم‌جهت تأیید می‌کنن"
                : signal.strength === "medium"
                  ? "متوسط: بعضی از اندیکاتورها تأیید می‌کنن"
                  : "ضعیف: فقط یه اندیکاتور سیگنال می‌ده"
            }
            className="cursor-help"
          >
            <Badge
              variant="outline"
              className="border-white/10 bg-white/5 py-1.5 text-sm text-muted-foreground"
            >
              قدرت: {STRENGTH_LABEL[signal.strength] || signal.strength}
            </Badge>
          </span>
          <Badge
            variant="outline"
            className="border-white/10 bg-white/5 py-1.5 font-mono text-sm text-muted-foreground"
          >
            {timeframe}
          </Badge>
        </div>
      )}
    </div>
  );
}
