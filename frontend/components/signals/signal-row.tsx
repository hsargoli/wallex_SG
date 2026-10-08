"use client";

import Link from "next/link";
import { TrendingUp, TrendingDown, Minus, AlertCircle, ArrowUpRight } from "lucide-react";
import type { BatchSignalItem } from "@/lib/api";
import { formatNumber, formatPrice } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Sparkline } from "./sparkline";
import { cn } from "@/lib/utils";

const SIGNAL_CONFIG = {
  buy: {
    label: "خرید",
    icon: TrendingUp,
    text: "text-emerald-400",
    bg: "bg-emerald-500/15 border-emerald-500/30",
    bar: "bg-emerald-500",
    rail: "border-r-emerald-500/50",
    hover: "hover:border-r-emerald-500/80 hover:bg-emerald-500/[0.04]",
  },
  sell: {
    label: "فروش",
    icon: TrendingDown,
    text: "text-red-400",
    bg: "bg-red-500/15 border-red-500/30",
    bar: "bg-red-500",
    rail: "border-r-red-500/50",
    hover: "hover:border-r-red-500/80 hover:bg-red-500/[0.04]",
  },
  hold: {
    label: "بی‌طرف",
    icon: Minus,
    text: "text-zinc-400",
    bg: "bg-zinc-500/15 border-zinc-500/30",
    bar: "bg-zinc-500",
    rail: "border-r-zinc-500/30",
    hover: "hover:border-r-zinc-500/60 hover:bg-zinc-500/[0.04]",
  },
} as const;

const STRENGTH_LABELS: Record<string, string> = {
  weak: "ضعیف",
  medium: "متوسط",
  strong: "قوی",
};

/**
 * ترجمه‌ی دلیل‌های فنی به زبان ساده برای تازه‌کار.
 * کلید = متن دقیقی که backend می‌فرستد (یا بخشی از آن).
 * مقدار = جمله‌ی ساده.
 * اگر دلیل در دیکشنری نبود، خود متن اصلی نمایش داده می‌شود.
 */
const REASON_TRANSLATIONS: Array<[string, string]> = [
  // MACD
  ["MACD > Signal", "نشانه‌ی شروع حرکت صعودی"],
  ["MACD < Signal", "نشانه‌ی شروع حرکت نزولی"],
  // Bollinger
  ["نیمه‌ی بالایی باند", "قیمت در ناحیه‌ی بالای نوسان اخیر"],
  ["نیمه‌ی پایینی باند", "قیمت در ناحیه‌ی پایین نوسان اخیر"],
  ["بالای باند", "قیمت به‌طور غیرعادی بالا رفته"],
  ["زیر باند", "قیمت به‌طور غیرعادی پایین افتاده"],
  // RSI
  ["RSI < 30", "قیمت زیادی افتاده — احتمال برگشت"],
  ["RSI > 70", "قیمت زیادی بالا رفته — احتمال افت"],
  ["RSI", "قدرت خرید و فروش متعادل"],
  // EMA
  ["EMA fast > EMA slow", "روند کلی صعودی"],
  ["EMA fast < EMA slow", "روند کلی نزولی"],
  ["EMA", "میانگین قیمت در حال تغییر"],
  // ADX
  ["ADX > 20", "بازار جهت مشخصی دارد"],
  ["ADX < 20", "بازار بی‌جهت است — احتیاط"],
  ["ADX", "قدرت روند نامشخص"],
  // Volume
  ["Volume high", "حجم معاملات بالاست"],
  ["Volume low", "حجم معاملات کم — احتیاط"],
  ["حجم بالا", "حجم معاملات بالاست"],
  ["حجم پایین", "حجم معاملات پایین — احتیاط"],
  // Trend
  ["Uptrend", "روند صعودی"],
  ["Downtrend", "روند نزولی"],
  ["uptrend", "روند صعودی"],
  ["downtrend", "روند نزولی"],
  // fallback
  ["هیچ قانونی فعال نیست", "نشانه‌ی واضحی دیده نمی‌شود"],
  ["سیگنال متضاد", "نشانه‌ها با هم متناقض‌اند — صبر کن"],
  ["داده کافی نیست", "داده‌ی کافی برای تصمیم وجود ندارد"],
];

/** دلیل فنی را به زبان ساده ترجمه می‌کند. */
function humanizeReason(reason: string): string {
  for (const [key, value] of REASON_TRANSLATIONS) {
    if (reason.includes(key)) return value;
  }
  return reason;
}

interface SignalRowProps {
  signal: BatchSignalItem;
  quote?: string;
}

export function SignalRow({ signal, quote = "TMN" }: SignalRowProps) {
  if (signal.error) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-red-500/20 bg-red-500/[0.03] px-3 py-3">
        <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
        <div className="min-w-0 flex-1">
          <p className="font-mono text-sm font-bold">{signal.symbol}</p>
          <p className="truncate text-[10px] text-red-400/70">خطا: {signal.error}</p>
        </div>
      </div>
    );
  }

  const config = SIGNAL_CONFIG[signal.signal] || SIGNAL_CONFIG.hold;
  const Icon = config.icon;
  const confidence = Math.max(0, Math.min(100, signal.confidence));
  const c24 = signal.change_24h;
  const c7 = signal.change_7d;

  return (
    <Link
      href={`/signals/${signal.symbol}`}
      className={cn(
        "group flex items-center gap-3 rounded-lg border border-border/50 border-r-2 bg-card px-3 py-3 transition-all",
        config.rail,
        config.hover,
      )}
    >
      {/* Signal icon */}
      <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border", config.bg)}>
        <Icon className={cn("h-4 w-4", config.text)} />
      </div>

      {/* Symbol + price + reason */}
      <div className="min-w-[220px] max-w-[340px] shrink-0">
        <p className="font-mono text-sm font-bold">{signal.symbol}</p>
        <p className="font-mono text-[10px] text-muted-foreground">
          {formatPrice(signal.current_price)}{" "}
          <span className="text-[9px] opacity-60">{quote}</span>
        </p>
        {signal.reasons && signal.reasons.length > 0 && (
          <p className="mt-1 truncate text-[10px] leading-relaxed">
            <span className={cn("font-bold", config.text)}>چرا؟</span>
            <span className="mx-1 text-muted-foreground/60">·</span>
            <span className="text-muted-foreground">
              {signal.reasons.slice(0, 2).map(humanizeReason).join(" · ")}
            </span>
          </p>
        )}
      </div>

      {/* Sparkline */}
      <div className="hidden md:block">
        <Sparkline data={signal.sparkline} width={70} height={26} />
      </div>

      {/* Change 24h */}
      <div className="hidden w-16 shrink-0 text-right lg:block">
        <p className={cn("font-mono text-xs font-bold", c24 === null ? "text-muted-foreground" : c24 >= 0 ? "text-emerald-400" : "text-red-400")}>
          {c24 === null ? "—" : `${c24 >= 0 ? "+" : ""}${c24.toFixed(2)}%`}
        </p>
        <p className="text-[9px] text-muted-foreground">24h</p>
      </div>

      {/* Change 7d */}
      <div className="hidden w-16 shrink-0 text-right lg:block">
        <p className={cn("font-mono text-xs font-bold", c7 === null ? "text-muted-foreground" : c7 >= 0 ? "text-emerald-400" : "text-red-400")}>
          {c7 === null ? "—" : `${c7 >= 0 ? "+" : ""}${c7.toFixed(2)}%`}
        </p>
        <p className="text-[9px] text-muted-foreground">7d</p>
      </div>

      {/* Confidence + bar */}
      <div className="hidden min-w-[110px] shrink-0 items-center gap-2 md:flex">
        <span className={cn("font-mono text-xs font-bold", config.text)}>
          {confidence}
        </span>
        <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/5">
          <div className={cn("h-full rounded-full", config.bar)} style={{ width: `${confidence}%` }} />
        </div>
      </div>

      {/* Signal + strength badges */}
      <div className="mr-auto flex shrink-0 items-center gap-1.5">
        <Badge variant="outline" className={cn("text-[10px] border", config.bg, config.text)}>
          {config.label}
        </Badge>
        <Badge variant="outline" className="border-white/10 bg-white/5 text-[10px] text-muted-foreground">
          {STRENGTH_LABELS[signal.strength] || signal.strength}
        </Badge>
        <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
      </div>
    </Link>
  );
}
