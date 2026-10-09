"use client";

import { Activity, ArrowDown } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface TechnicalSnapshotProps {
  indicators: Record<string, string | null> | null | undefined;
  currentPrice: string | number | null;
}

function tone(v: number | null, pos: number, neg: number): string {
  if (v === null) return "text-muted-foreground";
  if (v >= pos) return "text-emerald-400";
  if (v <= neg) return "text-red-400";
  return "text-foreground";
}

export function TechnicalSnapshot({ indicators, currentPrice }: TechnicalSnapshotProps) {
  const num = (k: string): number | null => {
    const v = indicators?.[k];
    if (v === null || v === undefined) return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  };

  const ema9 = num("ema_9");
  const ema21 = num("ema_21");
  const macdHist = num("macd_hist");
  const rsi = num("rsi_14");
  const atr14 = num("atr_14");
  const bbUpper = num("bb_upper");
  const bbLower = num("bb_lower");
  const price = currentPrice !== null ? Number(currentPrice) : null;

  const emaDiff =
    ema9 !== null && ema21 !== null && ema21 > 0
      ? ((ema9 - ema21) / ema21) * 100
      : null;

  const bbPct =
    price !== null && bbUpper !== null && bbLower !== null && bbUpper > bbLower
      ? ((price - bbLower) / (bbUpper - bbLower)) * 100
      : null;

  const atrPct =
    atr14 !== null && price !== null && price > 0
      ? (atr14 / price) * 100
      : null;

  const cells = [
    {
      label: "EMA 9/21",
      value:
        emaDiff === null
          ? "—"
          : `${emaDiff >= 0 ? "+" : ""}${emaDiff.toFixed(2)}%`,
      tone: tone(emaDiff, 0.1, -0.1),
      hint: "اختلاف میانگین متحرک ۹ و ۲۱ — مثبت = صعودی",
    },
    {
      label: "MACD Hist",
      value:
        macdHist === null
          ? "—"
          : `${macdHist >= 0 ? "↑" : "↓"} ${
              Math.abs(macdHist) >= 1
                ? macdHist.toFixed(2)
                : macdHist.toFixed(4)
            }`,
      tone:
        macdHist === null
          ? "text-muted-foreground"
          : macdHist >= 0
            ? "text-emerald-400"
            : "text-red-400",
      hint: "هیستوگرام MACD — مثبت = فشار خرید",
    },
    {
      label: "RSI (14)",
      value: rsi === null ? "—" : rsi.toFixed(1),
      tone:
        rsi === null
          ? "text-muted-foreground"
          : rsi >= 70
            ? "text-red-400"
            : rsi <= 30
              ? "text-emerald-400"
              : "text-foreground",
      hint: "زیر ۳۰ اشباع فروش، بالای ۷۰ اشباع خرید",
    },
    {
      label: "ATR%",
      value: atrPct === null ? "—" : `${atrPct.toFixed(2)}%`,
      tone:
        atrPct === null
          ? "text-muted-foreground"
          : atrPct < 0.5
            ? "text-zinc-400"
            : atrPct < 2
              ? "text-emerald-400"
              : "text-amber-400",
      hint: "نوسان میانگین به درصد قیمت",
    },
    {
      label: "BB%",
      value: bbPct === null ? "—" : `${bbPct.toFixed(0)}%`,
      tone:
        bbPct === null
          ? "text-muted-foreground"
          : bbPct < 20
            ? "text-emerald-400"
            : bbPct > 80
              ? "text-red-400"
              : "text-foreground",
      hint: "موقعیت قیمت در باند بولینگر — ۰٪ کف، ۱۰۰٪ سقف",
    },
  ];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Activity className="h-4 w-4 text-emerald-400" />
          نگاه سریع تکنیکال
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-5 gap-2">
          {cells.map((c) => (
            <div
              key={c.label}
              className="rounded-lg border border-border/50 bg-background/40 px-2 py-2.5 text-center transition-colors hover:border-emerald-500/20"
              title={c.hint}
            >
              <p className="text-[10px] text-muted-foreground">{c.label}</p>
              <p className={cn("mt-1 font-mono text-sm font-bold", c.tone)}>
                {c.value}
              </p>
            </div>
          ))}
        </div>

        {/* Anchor به IndicatorsGrid */}
        <button
          type="button"
          onClick={() => {
            document
              .getElementById("section-indicators")
              ?.scrollIntoView({ behavior: "smooth", block: "start" });
          }}
          className="mt-3 flex w-full items-center justify-center gap-1 rounded-md border border-dashed border-border/40 py-1.5 text-[10px] text-muted-foreground transition-colors hover:border-emerald-500/30 hover:bg-emerald-500/[0.03] hover:text-emerald-400"
        >
          <ArrowDown className="h-3 w-3" />
          جزئیات کامل اندیکاتورها
        </button>
      </CardContent>
    </Card>
  );
}
