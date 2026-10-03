"use client";

import { useState } from "react";
import Link from "next/link";
import { TrendingUp, TrendingDown, RefreshCw, ExternalLink, Zap } from "lucide-react";
import { useCandles, useOrderBook } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import type { Timeframe } from "@/lib/api";
import { CandlestickChart } from "@/components/charts/candlestick-chart";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const TIMEFRAMES: Timeframe[] = ["15m", "1h", "4h", "1D"];

interface OrderBotChartProps {
  symbol: string;
}

export function OrderBotChart({ symbol }: OrderBotChartProps) {
  const [timeframe, setTimeframe] = useState<Timeframe>("1h");

  const candles = useCandles(symbol, timeframe, 300);
  const orderBook = useOrderBook(symbol);

  const lastCandle = candles.data?.candles?.at(-1);
  const prevCandle = candles.data?.candles?.at(-2);

  const currentPrice = lastCandle ? Number(lastCandle.close) : null;
  const prevPrice = prevCandle ? Number(prevCandle.close) : null;
  const change =
    currentPrice && prevPrice ? ((currentPrice - prevPrice) / prevPrice) * 100 : 0;
  const isUp = change >= 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex flex-wrap items-center justify-between gap-2 text-base">
          <div className="flex items-center gap-2">
            <span className="font-mono text-lg">{symbol}</span>
            {currentPrice && (
              <div className="flex items-center gap-2">
                <span className="font-mono text-xl font-bold text-amber-400">
                  {formatNumber(currentPrice)}
                </span>
                <span
                  className={cn(
                    "flex items-center gap-0.5 text-xs font-bold",
                    isUp ? "text-emerald-400" : "text-red-400",
                  )}
                >
                  {isUp ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  {isUp ? "+" : ""}
                  {change.toFixed(2)}%
                </span>
                <span className="text-[10px] text-muted-foreground">TMN</span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-1">
            {TIMEFRAMES.map((tf) => (
              <Button
                key={tf}
                variant="ghost"
                size="sm"
                onClick={() => setTimeframe(tf)}
                className={cn(
                  "h-7 px-2.5 font-mono text-xs",
                  timeframe === tf &&
                    "bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/20",
                )}
              >
                {tf}
              </Button>
            ))}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => candles.refetch()}
              disabled={candles.isFetching}
              className="h-7 px-2"
            >
              <RefreshCw
                className={cn(
                  "h-3.5 w-3.5",
                  candles.isFetching && "animate-spin",
                )}
              />
            </Button>
            <Link href={`/signals/${symbol}`}>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 gap-1.5 px-2.5 text-xs text-emerald-400 hover:bg-emerald-500/10 hover:text-emerald-300"
              >
                <Zap className="h-3.5 w-3.5" />
                سیگنال
                <ExternalLink className="h-3 w-3 opacity-60" />
              </Button>
            </Link>
          </div>
        </CardTitle>

        {/* Orderbook quick stats */}
        {orderBook.data && (
          <div className="mt-3 flex flex-wrap gap-4 text-xs">
            <div>
              <span className="text-muted-foreground">بهترین خرید: </span>
              <span className="font-mono text-emerald-400">
                {formatNumber(orderBook.data.best_bid || 0)}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">بهترین فروش: </span>
              <span className="font-mono text-red-400">
                {formatNumber(orderBook.data.best_ask || 0)}
              </span>
            </div>
            {orderBook.data.spread_pct && (
              <div>
                <span className="text-muted-foreground">اسپرد: </span>
                <span className="font-mono text-amber-400">
                  {Number(orderBook.data.spread_pct).toFixed(3)}%
                </span>
              </div>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent>
        {candles.isLoading ? (
          <Skeleton className="h-[500px] w-full" />
        ) : candles.isError ? (
          <div className="flex h-[500px] items-center justify-center text-sm text-red-400">
            خطا در دریافت داده‌ی نمودار
          </div>
        ) : candles.data?.candles?.length ? (
          <CandlestickChart candles={candles.data.candles} />
        ) : (
          <div className="flex h-[500px] items-center justify-center text-sm text-muted-foreground">
            داده‌ای برای نمایش نیست
          </div>
        )}
      </CardContent>
    </Card>
  );
}
