"use client";

import { useState } from "react";
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronDown,
  BookOpen,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { InfoTip } from "@/components/ui/info-tip";
import { cn } from "@/lib/utils";

interface TechnicalSnapshotDetailedProps {
  indicators: Record<string, string | null> | null | undefined;
  currentPrice: string | number | null;
  variant?: "advanced" | "beginner";
}

type Tone = "emerald" | "red" | "amber" | "zinc" | "blue";

const TONE_CLS: Record<Tone, { text: string; bar: string; border: string }> = {
  emerald: { text: "text-emerald-400", bar: "bg-emerald-500", border: "border-emerald-500/20" },
  red:     { text: "text-red-400",     bar: "bg-red-500",     border: "border-red-500/20" },
  amber:   { text: "text-amber-400",   bar: "bg-amber-500",   border: "border-amber-500/20" },
  zinc:    { text: "text-zinc-400",    bar: "bg-zinc-500",    border: "border-zinc-500/20" },
  blue:    { text: "text-blue-400",    bar: "bg-blue-500",    border: "border-blue-500/20" },
};

interface Cell {
  label: string;
  display: string;
  text: string;
  tone: Tone;
  bar: number | null;
  icon: "up" | "down" | "flat";
  hint: string;
  explain: string;
}

function interpretEMA(v: number | null): { text: string; tone: Tone; bar: number | null } {
  if (v === null) return { text: "داده‌ای نیست", tone: "zinc", bar: null };
  const bar = Math.max(0, Math.min(100, ((v + 3) / 6) * 100));
  if (v > 1) return { text: "صعودی قوی", tone: "emerald", bar };
  if (v > 0.1) return { text: "صعودی ملایم", tone: "emerald", bar };
  if (v > -0.1) return { text: "بی‌جهت", tone: "zinc", bar };
  if (v > -1) return { text: "نزولی ملایم", tone: "red", bar };
  return { text: "نزولی قوی", tone: "red", bar };
}

function interpretMACD(v: number | null): { text: string; tone: Tone; bar: number | null } {
  if (v === null) return { text: "داده‌ای نیست", tone: "zinc", bar: null };
  const abs = Math.abs(v);
  if (v > 0) return { text: abs > 50 ? "خریداران خیلی قوی" : "خریداران قوی", tone: "emerald", bar: 100 };
  if (v < 0) return { text: abs > 50 ? "فروشندگان خیلی قوی" : "فروشندگان قوی", tone: "red", bar: 0 };
  return { text: "متعادل", tone: "zinc", bar: 50 };
}

function interpretRSI(v: number | null): { text: string; tone: Tone; bar: number | null } {
  if (v === null) return { text: "داده‌ای نیست", tone: "zinc", bar: null };
  const bar = Math.max(0, Math.min(100, v));
  if (v < 30) return { text: "اشباع فروش — احتمال برگشت", tone: "emerald", bar };
  if (v < 45) return { text: "تمایل به خرید", tone: "emerald", bar };
  if (v <= 55) return { text: "متعادل", tone: "zinc", bar };
  if (v <= 70) return { text: "تمایل به فروش", tone: "amber", bar };
  return { text: "اشباع خرید — احتمال افت", tone: "red", bar };
}

function interpretATR(v: number | null): { text: string; tone: Tone; bar: number | null } {
  if (v === null) return { text: "داده‌ای نیست", tone: "zinc", bar: null };
  const bar = Math.max(0, Math.min(100, (v / 5) * 100));
  if (v < 1) return { text: "آرام — حرکت کم", tone: "blue", bar };
  if (v < 3) return { text: "نوسان متوسط", tone: "emerald", bar };
  if (v < 5) return { text: "پرنوسان — احتیاط", tone: "amber", bar };
  return { text: "خیلی پرنوسان — خطرناک", tone: "red", bar };
}

function interpretBB(v: number | null): { text: string; tone: Tone; bar: number | null } {
  if (v === null) return { text: "داده‌ای نیست", tone: "zinc", bar: null };
  const bar = Math.max(0, Math.min(100, v));
  if (v < 20) return { text: "نزدیک کف باند", tone: "emerald", bar };
  if (v < 40) return { text: "نیمه‌ی پایین", tone: "emerald", bar };
  if (v <= 60) return { text: "میانه‌ی باند", tone: "zinc", bar };
  if (v <= 80) return { text: "نیمه‌ی بالا", tone: "amber", bar };
  return { text: "نزدیک سقف باند", tone: "red", bar };
}

export function TechnicalSnapshotDetailed({
  indicators,
  currentPrice,
  variant = "advanced",
}: TechnicalSnapshotDetailedProps) {
  const [showExplain, setShowExplain] = useState(false);

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

  const L =
    variant === "beginner"
      ? {
          ema: "روند کوتاه‌مدت",
          macd: "قدرت خریداران",
          rsi: "اشباع خرید/فروش",
          atr: "نوسان",
          bb: "جایگاه قیمت",
        }
      : {
          ema: "EMA 9/21",
          macd: "MACD Hist",
          rsi: "RSI (14)",
          atr: "ATR%",
          bb: "BB%",
        };

  const cells: Cell[] = [
    {
      label: L.ema,
      display: emaDiff === null ? "—" : `${emaDiff >= 0 ? "+" : ""}${emaDiff.toFixed(2)}%`,
      ...interpretEMA(emaDiff),
      icon: emaDiff === null ? "flat" : emaDiff > 0.1 ? "up" : emaDiff < -0.1 ? "down" : "flat",
      hint: "اختلاف میانگین متحرک ۹ و ۲۱.",
      explain:
        "میانگین متحرک (EMA) نشون‌دهنده‌ی میانگین قیمت در بازه‌ی مشخصه. وقتی EMA 9 (کوتاه‌مدت) از EMA 21 (بلندمدت) بالاتر باشه، یعنی قیمت در کوتاه‌مدت داره سریع‌تر از بلندمدت رشد می‌کنه — نشانه‌ی روند صعودی. برعکسش روند نزولی. اگه دو تا نزدیک باشن، بازار بی‌جهته و بدون روند قویه.",
    },
    {
      label: L.macd,
      display:
        macdHist === null
          ? "—"
          : `${macdHist >= 0 ? "↑" : "↓"} ${Math.abs(macdHist) >= 1 ? macdHist.toFixed(2) : macdHist.toFixed(4)}`,
      ...interpretMACD(macdHist),
      icon: macdHist === null ? "flat" : macdHist > 0 ? "up" : macdHist < 0 ? "down" : "flat",
      hint: "هیستوگرام MACD — فشار خرید یا فروش.",
      explain:
        "MACD فشار خریداران و فروشندگان رو اندازه می‌گیره. عدد مثبت یعنی خریداران قوی‌تر از فروشندگانن و قیمت معمولاً در حال رشده. عدد منفی یعنی فروشندگان غالب‌اند. هرچی عدد بزرگ‌تر (به‌قدر مطلق)، فشار شدیدتر. تغییر علامت (مثبت به منفی) معمولاً هشدار تغییر رونده.",
    },
    {
      label: L.rsi,
      display: rsi === null ? "—" : rsi.toFixed(1),
      ...interpretRSI(rsi),
      icon: rsi === null ? "flat" : rsi < 45 ? "up" : rsi > 55 ? "down" : "flat",
      hint: "شاخص قدرت نسبی (۰-۱۰۰).",
      explain:
        "RSI نشون می‌ده قیمت چقدر از میانگین فاصله گرفته. زیر ۳۰ = بیش‌فروش (احتمال برگشت به بالا). بالای ۷۰ = بیش‌خرید (احتمال افت). بین ۴۰ تا ۶۰ = متعادل. نکته: در روندهای قوی، RSI می‌تونه مدت طولانی بالا یا پایین بمونه — تنها به RSI تصمیم نگیر.",
    },
    {
      label: L.atr,
      display: atrPct === null ? "—" : `${atrPct.toFixed(2)}%`,
      ...interpretATR(atrPct),
      icon: "flat",
      hint: "میانگین نوسان روزانه.",
      explain:
        "ATR نشون می‌ده این نماد معمولاً چقدر نوسان داره. زیر ۱٪ = حرکت آرام، مناسب تازه‌کار. ۱-۳٪ = طبیعی و متعادل. بالای ۳٪ = پرنوسان و پرخطر برای تازه‌کارها. برای محاسبه‌ی حد ضرر و حد سود هم از ATR استفاده می‌شه.",
    },
    {
      label: L.bb,
      display: bbPct === null ? "—" : `${bbPct.toFixed(0)}%`,
      ...interpretBB(bbPct),
      icon: bbPct === null ? "flat" : bbPct < 40 ? "up" : bbPct > 60 ? "down" : "flat",
      hint: "موقعیت قیمت در باند بولینگر.",
      explain:
        "این عدد نشون می‌ده قیمت فعلی کجای باند بولینگر (Bollinger Bands) قرار داره. باند بولینگر محدوده‌ای حول میانگین ۲۰ کندل اخیر است (میانگین ± ۲ برابر انحراف معیار).\n\n📊 معنی اعداد:\n• ۰٪ = قیمت روی کف باند — پایین‌تر از حد معمول. معمولاً نشانه‌ی فرصت خرید یا ادامه‌ی سقوط.\n• ۵۰٪ = قیمت در میانه — وضعیت عادی و متعادل.\n• ۱۰۰٪ = قیمت روی سقف باند — بالاتر از حد معمول. احتمال افت یا ادامه‌ی رشد قوی.\n\n⚠️ نکته‌ی مهم: این عدد نسبت به ۲۰ کندل اخیره، نه سقف/کف تاریخی ارز. یعنی اگه ارزی یک سال پیش خیلی گرون‌تر بوده ولی الان فقط ۱۰٪ زیر سقف ۲۰ کندل اخیر باشه، این عدد بهت نمی‌گه که قیمت هنوز از سقف تاریخی فاصله‌ی زیادی داره. برای مقایسه‌ی تاریخی، باید به بازه‌های بلندمدت (۳ماهه، ۱ساله) در تب آمار نگاه کنی.",
    },
  ];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Activity className="h-4 w-4 text-emerald-400" />
          نگاه سریع تکنیکال
          <InfoTip text="پنج اندیکاتور کلیدی با تفسیر ساده. هر کارت مقدار + نوار + معنی رو نشون می‌ده." />
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* ۵ کارت */}
        <div className="grid grid-cols-2 gap-2.5">
          {cells.map((c, idx) => {
            const t = TONE_CLS[c.tone];
            const Icon =
              c.icon === "up" ? TrendingUp : c.icon === "down" ? TrendingDown : Minus;
            return (
              <div
                key={c.label}
                className={cn(
                  "rounded-lg border bg-background/40 p-3 transition-colors",
                  t.border,
                  idx === 4 && "col-span-2",
                )}
                title={c.hint}
              >
                <div className="flex items-center justify-between gap-1">
                  <p className="text-[11px] font-medium text-muted-foreground">
                    {c.label}
                  </p>
                  <Icon className={cn("h-3.5 w-3.5 shrink-0", t.text)} />
                </div>

                <p className={cn("mt-2 font-mono text-lg font-bold", t.text)}>
                  {c.display}
                </p>

                {c.bar !== null && (
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/5">
                    <div
                      className={cn("h-full rounded-full transition-all", t.bar)}
                      style={{ width: `${c.bar}%` }}
                    />
                  </div>
                )}

                <p className={cn("mt-2 text-[11px] font-medium leading-tight", t.text)}>
                  {c.text}
                </p>
              </div>
            );
          })}
        </div>

        {/* دکمه توضیح بیشتر */}
        <button
          type="button"
          onClick={() => setShowExplain((v) => !v)}
          className={cn(
            "mt-3 flex w-full items-center justify-center gap-1.5 rounded-md border border-dashed py-2 text-[11px] transition-colors",
            showExplain
              ? "border-emerald-500/40 bg-emerald-500/[0.05] text-emerald-400"
              : "border-border/40 text-muted-foreground hover:border-emerald-500/30 hover:bg-emerald-500/[0.03] hover:text-emerald-400",
          )}
        >
          <BookOpen className="h-3.5 w-3.5" />
          {showExplain ? "بستن توضیحات" : "توضیح کامل این ۵ اندیکاتور"}
          <ChevronDown
            className={cn(
              "h-3.5 w-3.5 transition-transform",
              showExplain && "rotate-180",
            )}
          />
        </button>

        {/* پنل توضیحات */}
        {showExplain && (
          <div className="mt-3 space-y-3 rounded-lg border border-border/40 bg-background/40 p-4">
            {cells.map((c) => {
              const t = TONE_CLS[c.tone];
              return (
                <div key={c.label} className="border-b border-border/30 pb-3 last:border-0 last:pb-0">
                  <p className={cn("mb-1 flex items-center gap-2 text-sm font-bold", t.text)}>
                    <span className={cn("h-1.5 w-1.5 rounded-full", t.bar)} />
                    {c.label}
                  </p>
                  <p className="text-[12px] leading-relaxed text-muted-foreground">
                    {c.explain}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
