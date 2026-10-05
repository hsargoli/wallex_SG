"use client";

import { cn } from "@/lib/utils";
import { InfoTip } from "@/components/ui/info-tip";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

type Signal = "bullish" | "bearish" | "neutral";

interface IndicatorCardProps {
  /** نام اندیکاتور — مثلاً RSI(14) */
  name: string;
  /** مقدار فعلی */
  value: string | number | null;
  /** وضعیت: صعودی / نزولی / بی‌طرف */
  signal: Signal;
  /** توضیح کوتاه برای tooltip */
  hint: string;
  /** متن وضعیت به فارسی */
  label: string;
  /** درصد پیشرفت (0-100) — اختیاری */
  progress?: number;
  /** راهنمای تفسیر — مثلاً «زیر ۳۰ اشباع فروش» */
  interpretation?: string;
}

const SIGNAL_STYLES: Record<Signal, { text: string; bg: string; icon: React.ElementType }> = {
  bullish: {
    text: "text-emerald-400",
    bg: "border-emerald-500/20 bg-emerald-500/[0.03]",
    icon: TrendingUp,
  },
  bearish: {
    text: "text-red-400",
    bg: "border-red-500/20 bg-red-500/[0.03]",
    icon: TrendingDown,
  },
  neutral: {
    text: "text-zinc-400",
    bg: "border-white/10 bg-white/[0.02]",
    icon: Minus,
  },
};

export function IndicatorCard({
  name,
  value,
  signal,
  hint,
  label,
  progress,
  interpretation,
}: IndicatorCardProps) {
  const s = SIGNAL_STYLES[signal];
  const Icon = s.icon;

  return (
    <div className={cn("rounded-xl border p-4", s.bg)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <p className="text-xs font-medium text-muted-foreground">{name}</p>
          <InfoTip text={hint} />
        </div>
        <Icon className={cn("h-4 w-4", s.text)} />
      </div>

      {/* Value */}
      <p className={cn("mt-2 font-mono text-xl font-bold", s.text)}>
        {value ?? "—"}
      </p>

      {/* Label */}
      <p className={cn("mt-0.5 text-[11px]", s.text)}>{label}</p>

      {/* Progress bar (اختیاری) */}
      {progress !== undefined && (
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/5">
          <div
            className={cn(
              "h-full transition-all",
              signal === "bullish"
                ? "bg-emerald-500"
                : signal === "bearish"
                  ? "bg-red-500"
                  : "bg-zinc-500",
            )}
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      )}

      {/* Interpretation */}
      {interpretation && (
        <p className="mt-2 text-[10px] leading-relaxed text-muted-foreground">
          {interpretation}
        </p>
      )}
    </div>
  );
}
