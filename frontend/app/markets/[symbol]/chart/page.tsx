"use client";

import { use, useState } from "react";
import Link from "next/link";
import { ArrowRight, TrendingUp, TrendingDown } from "lucide-react";
import { useCandles, useOrderBook } from "@/lib/queries";
import { type Timeframe } from "@/lib/api";
import { formatPrice, formatNumber } from "@/lib/format";
import { CandlestickChart } from "@/components/charts/candlestick-chart";
import { SymbolSwitcher } from "@/components/markets/symbol-switcher";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const TIMEFRAMES: Timeframe[] = ["15m", "1h", "4h", "1D"];

export default function ChartPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = use(params);
  const [timeframe, setTimeframe] = useState<Timeframe>("1h");

  const candlesQuery = useCandles(symbol, timeframe, 500);
  const bookQuery = useOrderBook(symbol);

  const candles = candlesQuery.data?.candles ?? [];
  const lastCandle = candles[candles.length - 1];
  const firstCandle = candles[0];

  const priceChange =
    lastCandle && firstCandle
      ? Number(lastCandle.close) - Number(firstCandle.open)
      : 0;
  const priceChangePct =
    firstCandle && Number(firstCandle.open) > 0
      ? (priceChange / Number(firstCandle.open)) * 100
      : 0;
  const isUp = priceChange >= 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-4">
        <Link
          href={`/markets/${symbol}`}
          className="flex h-9 w-9 items-center justify-center rounded-lg border transition hover:border-emerald-500/30 hover:bg-emerald-500/5"
        >
          <ArrowRight className="h-4 w-4" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <SymbolSwitcher
              current={symbol}
              basePath="/markets"
              suffix="/chart"
            />
            {lastCandle && (
              <span className="font-mono text-xl text-muted-foreground">
                {formatPrice(lastCandle.close)}
              </span>
            )}
            {priceChange !== 0 && (
              <span
                className={cn(
                  "flex items-center gap-1 rounded-md px-2 py-1 font-mono text-xs",
                  isUp
                    ? "bg-emerald-500/10 text-emerald-400"
                    : "bg-red-500/10 text-red-400",
                )}
              >
                {isUp ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                {isUp ? "+" : ""}
                {priceChangePct.toFixed(2)}%
              </span>
            )}
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {candles.length} کندل {timeframe}
          </p>
        </div>
      </div>

      {/* Chart */}
      <Card className="border-white/5 bg-[#0f0f17]">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 border-b border-white/5 pb-4">
          <CardTitle className="text-base">نمودار قیمت</CardTitle>
          <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-background/50 p-1">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={cn(
                  "rounded px-3 py-1.5 font-mono text-xs font-medium transition",
                  timeframe === tf
                    ? "bg-emerald-500/20 text-emerald-400"
                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
                )}
              >
                {tf}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <CandlestickChart candles={candles} loading={candlesQuery.isLoading} />
        </CardContent>
      </Card>

      {/* Snapshot + Link to order book */}
      <div className="grid gap-4 md:grid-cols-4">
        <StatBox
          label="بهترین خرید"
          value={bookQuery.data?.best_bid}
          accent="text-emerald-400"
        />
        <StatBox
          label="بهترین فروش"
          value={bookQuery.data?.best_ask}
          accent="text-red-400"
        />
        <StatBox
          label="اسپرد"
          value={bookQuery.data?.spread}
          accent="text-amber-400"
        />
        <Link
          href={`/markets/${symbol}`}
          className="flex items-center justify-center rounded-xl border border-white/10 bg-[#0f0f17] p-4 text-sm text-muted-foreground transition hover:border-emerald-500/30 hover:bg-emerald-500/5 hover:text-emerald-400"
        >
          مشاهده‌ی دفتر سفارشات ←
        </Link>
      </div>
    </div>
  );
}

function StatBox({
  label,
  value,
  accent,
}: {
  label: string;
  value?: string | null;
  accent: string;
}) {
  return (
    <div className="rounded-xl border border-white/5 bg-[#0f0f17] p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={cn("mt-1 font-mono text-lg font-bold", accent)}>
        {value ? formatPrice(value) : "—"}
      </p>
    </div>
  );
}
