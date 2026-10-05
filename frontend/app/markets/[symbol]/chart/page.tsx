"use client";

import { use, useMemo, useCallback, useState } from "react";
import Link from "next/link";
import { ArrowRight, TrendingUp, TrendingDown } from "lucide-react";
import { useCandles, useIndicators, useOrderBook, useMarket } from "@/lib/queries";
import { type Timeframe } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { ProChart } from "@/components/charts/pro-chart";
import {
  ChartLegend,
  type LegendData,
} from "@/components/charts/chart-legend";
import { ChartInfoCards } from "@/components/charts/chart-info-cards";
import { SymbolSwitcher } from "@/components/markets/symbol-switcher";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const TIMEFRAMES: Timeframe[] = ["15m", "1h", "4h", "1D"];

export default function ChartPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = use(params);
  const [timeframe, setTimeframe] = useState<Timeframe>("1h");
  const [showEMA, setShowEMA] = useState(true);
  const [showBB, setShowBB] = useState(false);
  const [showRSI, setShowRSI] = useState(true);
  const [showMACD, setShowMACD] = useState(true);
  const [legendData, setLegendData] = useState<LegendData | undefined>();
  const handleCrosshairMove = useCallback((d: LegendData | undefined) => {
    setLegendData(d);
  }, []);

  const candlesQuery = useCandles(symbol, timeframe, 500);
  const indicatorsQuery = useIndicators(symbol, timeframe, 500);
  const bookQuery = useOrderBook(symbol);
  const marketQuery = useMarket(symbol);

  const candles = useMemo(
    () => candlesQuery.data?.candles ?? [],
    [candlesQuery.data?.candles],
  );
  const lastCandle = candles[candles.length - 1];
  const firstCandle = candles[0];

  // محاسبات کارت‌ها
  const change24h = marketQuery.data?.daily_change_percent ?? null;
  const volume24h = marketQuery.data?.daily_volume ?? null;

  const volumeMa = useMemo(() => {
    const last20 = candles.slice(-20);
    if (last20.length === 0) return 0;
    return last20.reduce((sum, c) => sum + Number(c.volume || 0), 0) / last20.length;
  }, [candles]);
  const volumeRatio =
    volumeMa > 0 && lastCandle ? Number(lastCandle.volume || 0) / volumeMa : null;

  const lastOf = (arr?: (string | null)[]) =>
    arr && arr.length > 0 ? arr[arr.length - 1] : null;

  const ema9Value = lastOf(indicatorsQuery.data?.ema_9);
  const ema21Value = lastOf(indicatorsQuery.data?.ema_21);
  const macdHistValue = lastOf(indicatorsQuery.data?.macd_hist);

  const lastRsi = indicatorsQuery.data?.rsi_14;
  const rsiValue =
    lastRsi && lastRsi.length > 0
      ? (lastRsi[lastRsi.length - 1] as string | null)
      : null;

  const atrArr = indicatorsQuery.data?.atr_14;
  const lastAtr =
    atrArr && atrArr.length > 0 ? Number(atrArr[atrArr.length - 1] || 0) : 0;
  const lastPrice = lastCandle ? Number(lastCandle.close) : 0;
  const atrPct =
    lastPrice > 0 && lastAtr > 0
      ? ((lastAtr / lastPrice) * 100).toFixed(2)
      : null;

  const priceChange =
    lastCandle && firstCandle
      ? Number(lastCandle.close) - Number(firstCandle.open)
      : 0;
  const priceChangePct =
    firstCandle && Number(firstCandle.open) > 0
      ? (priceChange / Number(firstCandle.open)) * 100
      : 0;
  const isUp = priceChange >= 0;

  // آماده‌سازی indicators برای ProChart
  const indicators = useMemo(() => {
    const d = indicatorsQuery.data;
    if (!d) return undefined;
    return {
      ema9: d.ema_9,
      ema21: d.ema_21,
      bbUpper: d.bb_upper,
      bbMiddle: d.bb_middle,
      bbLower: d.bb_lower,
      rsi14: d.rsi_14,
      macd: d.macd,
      macdSignal: d.macd_signal,
      macdHist: d.macd_hist,
    };
  }, [indicatorsQuery.data]);

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
          <div className="flex flex-wrap items-center gap-3">
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

      {/* Info Cards */}
      <ChartInfoCards
        price={lastCandle?.close}
        change24h={change24h}
        volume24h={volume24h}
        volumeRatio={volumeRatio}
        atrPct={atrPct}
        rsi={rsiValue}
        ema9={ema9Value}
        ema21={ema21Value}
        macdHist={macdHistValue}
      />

      {/* Chart */}
      <Card className="border-white/5 bg-[#0f0f17]">
        <CardHeader className="flex flex-col gap-3 border-b border-white/5 pb-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle className="text-base">نمودار قیمت</CardTitle>

            {/* Timeframe buttons */}
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
          </div>

          {/* Layer toggles */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] text-muted-foreground">لایه‌ها:</span>
            <LayerToggle
              label="EMA 9/21"
              active={showEMA}
              onClick={() => setShowEMA(!showEMA)}
              color="text-emerald-400"
            />
            <LayerToggle
              label="Bollinger"
              active={showBB}
              onClick={() => setShowBB(!showBB)}
              color="text-purple-400"
            />
            <LayerToggle
              label="RSI (14)"
              active={showRSI}
              onClick={() => setShowRSI(!showRSI)}
              color="text-purple-400"
            />
            <LayerToggle
              label="MACD"
              active={showMACD}
              onClick={() => setShowMACD(!showMACD)}
              color="text-emerald-400"
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-3 pt-4">
          {/* Legend زنده */}
          <ChartLegend
            data={legendData}
            showEMA={showEMA}
            showBB={showBB}
            showRSI={showRSI}
            showMACD={showMACD}
          />

          {/* چارت */}
          <ProChart
            candles={candles}
            indicators={indicators}
            height={500}
            showVolume={true}
            showEMA={showEMA}
            showBB={showBB}
            showRSI={showRSI}
            showMACD={showMACD}
            loading={candlesQuery.isLoading || indicatorsQuery.isLoading}
            onCrosshairMove={handleCrosshairMove}
          />
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

function LayerToggle({
  label,
  active,
  onClick,
  color,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  color: string;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-md border px-2 py-1 font-mono text-[10px] transition",
        active
          ? cn("border-white/20 bg-white/5", color)
          : "border-white/5 bg-transparent text-muted-foreground/50 hover:border-white/10 hover:text-muted-foreground",
      )}
    >
      {label}
    </button>
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
