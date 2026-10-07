"use client";

import { useMemo } from "react";
import Link from "next/link";
import { RotateCw } from "lucide-react";
import { useCandles } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { BtcCandles, type Candle as ChartCandle } from "./btc-candles";

const SYMBOL = "BTCTMN";

export function BtcChartCard() {
  // v1 عمداً: candles-v2 کندل ساختگی (synthetic) هم برمی‌گرداند
  const q = useCandles(SYMBOL, "1h", 48);

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
  const last = ok ? candles[candles.length - 1].close : null;
  const ref = candles.length > 24 ? candles[candles.length - 25].close : null;
  const pct = last !== null && ref ? ((last - ref) / ref) * 100 : null;

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
          </>
        )}
      </CardContent>
    </Card>
  );
}
