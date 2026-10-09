"use client";

import {
  Wallet,
  BarChart3,
  Activity,
  Zap,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ChartInfoCardsProps {
  price?: string | null;
  change24h?: string | null;
  volume24h?: string | null;
  volumeRatio?: number | null; // نسبت به میانگین ۲۰
  atrPct?: string | null;
  rsi?: string | null;
  // برای محاسبه‌ی روند
  ema9?: string | null;
  ema21?: string | null;
  macdHist?: string | null;
}

function fmtNum(v?: string | null, digits = 2): string {
  if (!v) return "—";
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  const abs = Math.abs(n);
  // اعداد اعشاری (مثل PEPE = 1.0058)
  if (abs > 0 && abs < 1) {
    return n.toLocaleString("en-US", { maximumFractionDigits: 6 });
  }
  // اعداد بزرگ: همیشه کامل با جداکننده
  return n.toLocaleString("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  });
}

export function ChartInfoCards({
  price,
  change24h,
  volume24h,
  volumeRatio,
  atrPct,
  rsi,
  ema9,
  ema21,
  macdHist,
}: ChartInfoCardsProps) {
  // ─── محاسبه‌ی روند از EMA + MACD ───
  const trendResult = (() => {
    if (!price || !ema9 || !ema21) {
      return { label: "—", tone: "neutral" as const, score: 0, pattern: "" };
    }

    const p = Number(price);
    const e9 = Number(ema9);
    const e21 = Number(ema21);
    const hist = macdHist ? Number(macdHist) : null;

    let score = 0;
    if (e9 > e21) score += 1;
    if (e9 < e21) score -= 1;
    if (p > e21) score += 1;
    if (p < e21) score -= 1;
    if (hist !== null) {
      if (hist > 0) score += 1;
      if (hist < 0) score -= 1;
    }

    // فاصله‌ی EMA — الگو
    const emaGap = Math.abs((e9 - e21) / e21) * 100;
    const pattern =
      emaGap > 0.5
        ? "رونددار"
        : emaGap > 0.1
          ? "در حال تغییر"
          : "بازه‌ای";

    let label = "بی‌طرف";
    let tone: "bullish" | "bearish" | "neutral" = "neutral";
    if (score >= 2) {
      label = score >= 3 ? "صعودی قوی" : "صعودی";
      tone = "bullish";
    } else if (score <= -2) {
      label = score <= -3 ? "نزولی قوی" : "نزولی";
      tone = "bearish";
    }

    return { label, tone, score, pattern };
  })();
  const changeNum = change24h ? Number(change24h) : 0;
  const isUp = changeNum >= 0;

  const rsiNum = rsi ? Number(rsi) : null;
  const rsiState =
    rsiNum === null
      ? "—"
      : rsiNum >= 70
        ? "اشباع خرید"
        : rsiNum <= 30
          ? "اشباع فروش"
          : "نرمال";
  const rsiTone =
    rsiNum === null
      ? "neutral"
      : rsiNum >= 70
        ? "bearish"
        : rsiNum <= 30
          ? "bullish"
          : "neutral";

  const atrNum = atrPct ? Number(atrPct) : null;
  const atrState =
    atrNum === null
      ? "—"
      : atrNum > 3
        ? "پرنوسان"
        : atrNum < 1
          ? "کم‌نوسان"
          : "نرمال";
  const atrTone =
    atrNum === null
      ? "neutral"
      : atrNum > 3
        ? "bearish"
        : atrNum < 1
          ? "neutral"
          : "neutral";

  return (
    <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
      {/* قیمت */}
      <InfoCard
        icon={Wallet}
        label="قیمت"
        value={fmtNum(price, 0)}
        hint="آخرین قیمت معامله‌شده در والکس. با هر به‌روزرسانی، این عدد عوض می‌شه."
        tone="neutral"
        secondary={
          change24h ? (
            <span
              className={cn(
                "flex items-center gap-1 text-[11px] font-bold",
                isUp ? "text-emerald-400" : "text-red-400",
              )}
            >
              {isUp ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              {isUp ? "+" : ""}
              {changeNum.toFixed(2)}%
            </span>
          ) : null
        }
      />

      {/* حجم */}
      <InfoCard
        icon={BarChart3}
        label="حجم ۲۴h"
        value={fmtNum(volume24h, 0)}
        hint="مجموع حجم معاملات ۲۴ ساعت گذشته. هرچی بیشتر، بازار فعال‌تره."
        tone="neutral"
        secondary={
          volumeRatio !== null && volumeRatio !== undefined ? (
            <span
              className={cn(
                "font-mono text-[11px] font-bold",
                volumeRatio > 1.5
                  ? "text-emerald-400"
                  : volumeRatio < 0.5
                    ? "text-muted-foreground"
                    : "text-foreground",
              )}
            >
              {volumeRatio.toFixed(2)}× میانگین
            </span>
          ) : null
        }
      />

      {/* نوسان */}
      <InfoCard
        icon={Activity}
        label="نوسان (ATR)"
        value={atrPct ? `${Number(atrPct).toFixed(2)}%` : "—"}
        hint="میانگین نوسان ۱۴ دوره. بالاتر = قیمت سریع‌تر تغییر می‌کنه (ریسک بیشتر)."
        tone={atrTone}
        secondary={
          <span className="text-[11px] text-muted-foreground">{atrState}</span>
        }
      />

      {/* RSI */}
      <InfoCard
        icon={Zap}
        label="RSI (14)"
        value={rsiNum !== null ? rsiNum.toFixed(1) : "—"}
        hint="شاخص قدرت نسبی. بالای ۷۰: اشباع خرید (احتمال اصلاح). زیر ۳۰: اشباع فروش (احتمال رشد)."
        tone={rsiTone}
        secondary={
          <span className="text-[11px] text-muted-foreground">{rsiState}</span>
        }
      />

      {/* روند */}
      <InfoCard
        icon={
          trendResult.tone === "bullish"
            ? TrendingUp
            : trendResult.tone === "bearish"
              ? TrendingDown
              : Minus
        }
        label="روند"
        value={trendResult.label}
        hint="ترکیب ۳ نشانگر: EMA9 vs EMA21، قیمت vs EMA21، و MACD Histogram. هر چی امتیاز بالاتر، روند قوی‌تر."
        tone={trendResult.tone}
        secondary={
          trendResult.score !== 0 ? (
            <span className="font-mono text-[11px] text-muted-foreground">
              امتیاز {trendResult.score > 0 ? "+" : ""}
              {trendResult.score} · {trendResult.pattern}
            </span>
          ) : null
        }
      />
    </div>
  );
}

const TONES = {
  bullish: {
    border: "border-emerald-500/20",
    bg: "bg-emerald-500/[0.03]",
    icon: "bg-emerald-500/15 text-emerald-400",
    text: "text-emerald-400",
  },
  bearish: {
    border: "border-red-500/20",
    bg: "bg-red-500/[0.03]",
    icon: "bg-red-500/15 text-red-400",
    text: "text-red-400",
  },
  neutral: {
    border: "border-white/10",
    bg: "bg-white/[0.02]",
    icon: "bg-white/5 text-muted-foreground",
    text: "text-foreground",
  },
} as const;

function InfoCard({
  icon: Icon,
  label,
  value,
  hint,
  tone,
  secondary,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  hint: string;
  tone: keyof typeof TONES;
  secondary?: React.ReactNode;
}) {
  const t = TONES[tone];
  return (
    <div
      title={hint}
      className={cn(
        "cursor-help rounded-xl border p-3 transition-all hover:shadow-lg",
        t.border,
        t.bg,
      )}
    >
      <div className="flex items-center gap-1.5">
        <div
          className={cn(
            "flex h-6 w-6 items-center justify-center rounded-md",
            t.icon,
          )}
        >
          <Icon className="h-3.5 w-3.5" />
        </div>
        <p className="text-[10px] text-muted-foreground">{label}</p>
      </div>
      <p className={cn("mt-1.5 font-mono text-base font-bold", t.text)}>
        {value}
      </p>
      {secondary && <div className="mt-1">{secondary}</div>}
    </div>
  );
}
