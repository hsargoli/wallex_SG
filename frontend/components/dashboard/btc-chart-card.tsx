"use client";

import { useMemo, useState, useEffect } from "react";
import Link from "next/link";
import { RotateCw } from "lucide-react";
import { useCandles, useMarkets } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { BtcCandles, type Candle as ChartCandle } from "./btc-candles";

const SYMBOL = "BTCTMN";

const SARV_TIPS = [
  "صبر در بازارهای مالی، کلید اصلی سودآوری است. سرو هم در سکوت رشد می‌کند.",
  "نوسانات کوتاه‌مدت، بخشی طبیعی از چرخه بازار هستند. نگران بادهای زودگذر نباش.",
  "همیشه قبل از ورود به معامله، حد ضرر (Stop Loss) خود را مشخص کنید.",
  "در اوج هیجان خرید و ترس از فروش، هرگز تصمیمات احساسی نگیرید.",
  "روند اصلی بازار دوست شماست؛ سعی نکنید در خلاف جهت روند حرکت کنید."
];

export function BtcChartCard() {
  // v1 عمداً: candles-v2 کندل ساختگی (synthetic) هم برمی‌گرداند
  const [dailyTip, setDailyTip] = useState("");

  useEffect(() => {
    setDailyTip(SARV_TIPS[Math.floor(Math.random() * SARV_TIPS.length)]);
  }, []);

  const q = useCandles(SYMBOL, "1h", 48);
  const markets = useMarkets();
  const ticker = markets.data?.items?.find((m) => m.symbol === SYMBOL);

  // api فیلدها را رشته می‌دهد؛ اینجا عدد می‌شوند و بر اساس زمان مرتب
  const candles: ChartCandle[] = useMemo(() => {
    const raw = q.data?.candles ?? [];
    return [...raw]
      .sort((a, b) => a.time - b.time)
      .map((k) => ({
        open: Number(k.open),
        high: Number(k.high),
        low: Number(k.low),
        close: Number(k.close),
      }));
  }, [q.data]);

  const ok = candles.length >= 2;
  // قیمت و درصد از تیکر زنده (همان منبع «بازارهای داغ»)؛ اگر نبود از کندل‌ها
  const tLast = Number(ticker?.last_price);
  const tPct = Number(ticker?.daily_change_percent);
  const cLast = ok ? candles[candles.length - 1].close : null;
  const cRef = candles.length > 24 ? candles[candles.length - 25].close : null;
  const last = Number.isFinite(tLast) && tLast > 0 ? tLast : cLast;
  const pct =
    ticker?.daily_change_percent != null && Number.isFinite(tPct)
      ? tPct
      : cLast !== null && cRef
        ? ((cLast - cRef) / cRef) * 100
        : null;

  return (
    <Card className="shadow-[0_0_70px_-20px_var(--wx-glow)]">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span>بیت‌کوین · ۱ ساعته</span>
          <Link
            href={"/markets/" + SYMBOL + "/chart"}
            className="text-xs font-normal text-muted-foreground hover:text-foreground"
          >
            چارت کامل
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {q.isLoading ? (
          <Skeleton className="h-[220px] w-full rounded-xl" />
        ) : q.isError || !ok ? (
          <div className="flex flex-col items-center gap-2 py-10 text-sm text-muted-foreground">
            <span>داده‌ی کندل بیت‌کوین دریافت نشد.</span>
            <button
              type="button"
              onClick={() => q.refetch()}
              className="inline-flex items-center gap-1 text-amber-500 hover:underline"
            >
              <RotateCw className="h-3.5 w-3.5" />
              تلاش دوباره
            </button>
          </div>
        ) : (
          <>
            <div className="mb-2 flex items-baseline gap-3">
              <span dir="ltr" className="font-mono text-xl font-bold">
                {formatNumber(last as number, { maximumFractionDigits: 0 })}
              </span>
              <span className="text-xs text-muted-foreground">تومان</span>
              {pct !== null && (
                <span
                  dir="ltr"
                  className="font-mono text-sm font-bold"
                  style={{ color: pct >= 0 ? "var(--wx-up)" : "var(--wx-down)" }}
                >
                  {(pct >= 0 ? "+" : "") + pct.toFixed(2) + "%"}
                </span>
              )}
              {pct !== null && (
                <span className="text-xs text-muted-foreground">۲۴ ساعت</span>
              )}
            </div>
            <BtcCandles candles={candles} />
            
            {/* 🌲 Sarv Tree Analysis */}
            <div className="mt-4 flex items-start gap-4 rounded-xl border border-violet-500/20 bg-gradient-to-br from-violet-500/10 to-transparent p-4">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className="shrink-0 mt-1 drop-shadow-[0_0_8px_rgba(52,211,153,0.4)]">
                <rect x="15" y="24" width="2" height="6" fill="#8B5A2B" rx="1" />
                <polygon points="16,23 6,14 26,14" fill="#059669" />
                <polygon points="16,17 8,9 24,9" fill="#10B981" />
                <polygon points="16,11 10,3 22,3" fill="#34D399" />
              </svg>
              <div className="space-y-1.5">
                <p className="text-sm font-bold text-foreground">
                  بیت‌کوین هم مثل سرو همیشه سبز بوده
                </p>
                <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground/80">
                  <span className="inline-block h-1 w-1 rounded-full bg-emerald-500"></span>
                  {dailyTip}
                </div>
              </div>
            </div>
            </>
                  ) : pct < -0.5 ? (
                    <>
                      <strong className="text-rose-400 font-semibold">سرو خمیده:</strong> امروز باد تندی در بازار وزیده و سرو کمی خم شده است. اما به یاد داشته باش که سرو در برابر طوفان‌ها مقاوم است. اصلاح قیمت بخشی از چرخه طبیعی بازار است.
                      <span className="block mt-1 text-[10px] text-muted-foreground/70">🌱 آموزش: اصلاح قیمت (Pullback) فرصتی برای خرید در قیمت‌های بهتر است.</span>
                    </>
                  ) : (
                    <>
                      <strong className="text-amber-400 font-semibold">سرو آرام:</strong> بازار امروز در حال استراحت است. مثل سرو در یک روز آرام و بی‌باد، در سکوت ریشه‌های خود را محکم می‌کند. منتظر بمان و بازار را زیر نظر بگیر.
                      <span className="block mt-1 text-[10px] text-muted-foreground/70">🌱 آموزش: در بازار خنثی، صبر و نظاره‌گری کلید موفقیت است.</span>
                    </>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
