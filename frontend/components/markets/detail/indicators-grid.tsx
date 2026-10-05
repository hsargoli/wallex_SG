"use client";

import { IndicatorCard } from "./indicator-card";
import { type IndicatorsResponse } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

interface IndicatorsGridProps {
  data?: IndicatorsResponse;
  loading?: boolean;
}

function last(arr: (string | null)[] | undefined): number | null {
  if (!arr || arr.length === 0) return null;
  const v = arr[arr.length - 1];
  return v === null ? null : Number(v);
}

export function IndicatorsGrid({ data, loading }: IndicatorsGridProps) {
  if (loading || !data) {
    return (
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  // آخرین قیمت
  const lastCandle = data.candles[data.candles.length - 1];
  const price = lastCandle ? Number(lastCandle.close) : 0;

  // آخرین مقادیر اندیکاتورها
  const ema7 = last(data.ema_9); // اسم نزدیک
  const ema21 = last(data.ema_21);
  const rsi = last(data.rsi_14);
  const macd = last(data.macd);
  const macdSignal = last(data.macd_signal);
  const macdHist = last(data.macd_hist);
  const bbUpper = last(data.bb_upper);
  const bbLower = last(data.bb_lower);
  const bbMiddle = last(data.bb_middle);
  const atr = last(data.atr_14);
  const volMa20 = last(data.volume_ma_20);

  // ─── RSI ───
  const rsiSignal =
    rsi === null ? "neutral" : rsi >= 70 ? "bearish" : rsi <= 30 ? "bullish" : "neutral";
  const rsiLabel =
    rsi === null
      ? "—"
      : rsi >= 70
        ? "اشباع خرید (بیش‌خرید)"
        : rsi <= 30
          ? "اشباع فروش (کم‌خرید)"
          : "نرمال";

  // ─── EMA21 vs قیمت ───
  const ema21Signal =
    ema21 === null || price === 0 ? "neutral" : price > ema21 ? "bullish" : "bearish";
  const ema21Label =
    ema21 === null
      ? "—"
      : price > ema21
        ? "قیمت بالای EMA (روند صعودی)"
        : "قیمت زیر EMA (روند نزولی)";

  // ─── MACD ───
  const macdSignalState =
    macd === null || macdSignal === null
      ? "neutral"
      : macdHist !== null && macdHist > 0
        ? "bullish"
        : "bearish";
  const macdLabel =
    macd === null || macdSignal === null
      ? "—"
      : macdHist !== null && macdHist > 0
        ? "MACD بالای Signal (صعودی)"
        : "MACD زیر Signal (نزولی)";

  // ─── Bollinger ───
  const bbPosition =
    bbUpper !== null && bbLower !== null && price > 0
      ? ((price - bbLower) / (bbUpper - bbLower)) * 100
      : null;
  const bbSignal =
    bbPosition === null
      ? "neutral"
      : bbPosition >= 80
        ? "bearish"
        : bbPosition <= 20
          ? "bullish"
          : "neutral";
  const bbLabel =
    bbPosition === null
      ? "—"
      : bbPosition >= 80
        ? "نزدیک باند بالا"
        : bbPosition <= 20
          ? "نزدیک باند پایین"
          : "نیمه‌ی میانی";

  // ─── ATR% (نوسان) ───
  const atrPct = atr !== null && price > 0 ? (atr / price) * 100 : null;
  const atrSignal =
    atrPct === null ? "neutral" : atrPct > 3 ? "bearish" : atrPct < 1 ? "bullish" : "neutral";
  const atrLabel =
    atrPct === null
      ? "—"
      : atrPct > 3
        ? "نوسان بالا (ریسکی)"
        : atrPct < 1
          ? "نوسان پایین (آروم)"
          : "نوسان نرمال";

  // ─── Volume vs MA20 ───
  const volValue = lastCandle ? Number(lastCandle.volume) : 0;
  const volRatio = volMa20 !== null && volMa20 > 0 ? volValue / volMa20 : null;
  const volSignal =
    volRatio === null ? "neutral" : volRatio > 1.5 ? "bullish" : volRatio < 0.5 ? "bearish" : "neutral";
  const volLabel =
    volRatio === null
      ? "—"
      : `${volRatio.toFixed(2)}× میانگین ۲۰`;

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <IndicatorCard
        name="RSI (14)"
        value={rsi !== null ? rsi.toFixed(1) : "—"}
        signal={rsiSignal}
        label={rsiLabel}
        progress={rsi ?? undefined}
        hint="شاخص قدرت نسبی (۱۴ دوره). بالای ۷۰: اشباع خرید (احتمال اصلاح). زیر ۳۰: اشباع فروش (احتمال رشد). ۳۰-۷۰: نرمال."
        interpretation="زیر ۳۰ فرصت خرید، بالای ۷۰ احتیاط"
      />

      <IndicatorCard
        name="EMA (21)"
        value={ema21 !== null ? ema21.toLocaleString("en-US", { maximumFractionDigits: 4 }) : "—"}
        signal={ema21Signal}
        label={ema21Label}
        hint="میانگین متحرک نمایی ۲۱ دوره. قیمت بالای EMA: روند صعودی. زیر EMA: روند نزولی."
        interpretation={
          ema21 !== null && price > 0
            ? `${(((price - ema21) / ema21) * 100).toFixed(2)}% فاصله از قیمت`
            : undefined
        }
      />

      <IndicatorCard
        name="MACD"
        value={macd !== null ? macd.toFixed(4) : "—"}
        signal={macdSignalState}
        label={macdLabel}
        hint="میانگین متحرک همگرا/واگرا. وقتی MACD بالای Signal باشه، مومنتوم صعودی. پایین: نزولی."
        interpretation={
          macdHist !== null
            ? `Histogram: ${macdHist.toFixed(4)}`
            : undefined
        }
      />

      <IndicatorCard
        name="Bollinger Bands"
        value={bbPosition !== null ? `${bbPosition.toFixed(0)}%` : "—"}
        signal={bbSignal}
        label={bbLabel}
        progress={bbPosition ?? undefined}
        hint="باند بولینگر: قیمت بین باند بالا و پایین نوسان می‌کنه. نزدیک باند بالا: اشباع خرید. نزدیک باند پایین: اشباع فروش."
        interpretation={
          bbUpper !== null && bbLower !== null
            ? `بازه: ${bbLower.toLocaleString("en-US", { maximumFractionDigits: 2 })} — ${bbUpper.toLocaleString("en-US", { maximumFractionDigits: 2 })}`
            : undefined
        }
      />

      <IndicatorCard
        name="ATR (14)"
        value={atrPct !== null ? `${atrPct.toFixed(2)}%` : "—"}
        signal={atrSignal}
        label={atrLabel}
        hint="میانگین دامنه واقعی — نوسان قیمت. بالاتر = نوسان بیشتر (ریسک بالاتر). پایین‌تر = آروم‌تر."
        interpretation="برای تعیین حد ضرر مناسب استفاده می‌شه"
      />

      <IndicatorCard
        name="حجم vs میانگین"
        value={volRatio !== null ? `${volRatio.toFixed(2)}×` : "—"}
        signal={volSignal}
        label={volLabel}
        progress={volRatio !== null ? Math.min(200, volRatio * 50) : undefined}
        hint="حجم معاملات فعلی به میانگین ۲۰ دوره. بالای ۱.۵×: حجم غیرعادی (احتمال حرکت). زیر ۰.۵×: حجم کم (بی‌تحرک)."
        interpretation="حجم بالا همراه با سیگنال = تأیید قوی‌تر"
      />
    </div>
  );
}
