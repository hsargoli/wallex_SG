"use client";

import { use, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  LineChart,
  TrendingUp,
  TrendingDown,
  Star,
  Activity,
  BarChart3,
} from "lucide-react";
import {
  useOrderBook,
  useMarket,
  useCandles,
  useIndicators,
  useSignal,
  useMultiTfSignals,
  useLevels,
} from "@/lib/queries";
import { useFavorites } from "@/lib/hooks/use-favorites";
import { formatNumber, formatPrice } from "@/lib/format";
import type { Timeframe } from "@/lib/api";
import { MiniChart } from "@/components/charts/mini-chart";
import { MarketStats } from "@/components/markets/market-stats";
import { OrderBookSummary } from "@/components/markets/order-book-summary";
import { IndicatorsGrid } from "@/components/markets/detail/indicators-grid";
import { SignalsChart } from "@/components/signals/signals-chart";
import { SignalCta } from "@/components/signals/detail/signal-cta";
import { ConfluenceCard } from "@/components/signals/detail/confluence-card";
import { MultiTfCard } from "@/components/signals/detail/multi-tf-card";
import { RuleRow } from "@/components/signals/detail/rule-row";
import { LevelsPanel } from "@/components/signals/levels-panel";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const TIMEFRAMES: Timeframe[] = ["15m", "1h", "4h", "1D"];

export default function SymbolPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = use(params);
  const [timeframe, setTimeframe] = useState<Timeframe>("1h");

  const market = useMarket(symbol);
  const book = useOrderBook(symbol);
  const candles = useCandles(symbol, timeframe, 200);
  const indicators = useIndicators(symbol, timeframe, 300);
  const signal = useSignal(symbol, timeframe);
  const multi = useMultiTfSignals(symbol);
  const levels = useLevels(symbol, timeframe);
  const { isFavorite, toggle, mounted } = useFavorites();
  const [tab, setTab] = useState<"analysis" | "trade">("analysis");

  const change = Number(market.data?.daily_change_percent || 0);
  const isUp = change >= 0;
  const fav = mounted && isFavorite(symbol);

  return (
    <div className="space-y-6">
      {/* ============================================================ */}
      {/* Header */}
      {/* ============================================================ */}
      <div className="flex flex-wrap items-center gap-4">
        <Link
          href="/markets"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border transition hover:border-emerald-500/30 hover:bg-emerald-500/5"
          aria-label="بازگشت"
        >
          <ArrowRight className="h-4 w-4" />
        </Link>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="font-mono text-2xl font-bold tracking-tight">
              {symbol}
            </h1>
            {market.data && (
              <Badge variant="outline" className="text-[10px]">
                {market.data.base_asset} / {market.data.quote_asset}
              </Badge>
            )}
          </div>
          {market.data && (
            <p className="mt-0.5 truncate text-sm text-muted-foreground">
              {market.data.fa_name || market.data.en_name || "—"}
            </p>
          )}
        </div>

        {/* Price + change (inline) */}
        {market.data && (
          <div className="hidden items-center gap-3 md:flex">
            <div className="text-left">
              <p className="font-mono text-xl font-bold leading-tight">
                {market.data.last_price
                  ? formatPrice(market.data.last_price)
                  : "—"}
              </p>
              <p
                className={cn(
                  "flex items-center gap-1 font-mono text-xs font-bold",
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
              </p>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => toggle(symbol)}
            className={cn(
              "h-9 w-9",
              fav
                ? "text-amber-400 border-amber-500/30"
                : "text-muted-foreground",
            )}
            aria-label={fav ? "حذف از علاقه‌مندی‌ها" : "افزودن به علاقه‌مندی‌ها"}
          >
            <Star className={cn("h-4 w-4", fav && "fill-current")} />
          </Button>
          <Link href={`/markets/${symbol}/chart`}>
            <Button className="gap-2 bg-emerald-600 hover:bg-emerald-700">
              <LineChart className="h-4 w-4" />
              مشاهده‌ی چارت کامل
            </Button>
          </Link>
        </div>
      </div>

      {/* ============================================================ */}
      {/* 24h stats */}
      {/* ============================================================ */}
      <MarketStats market={market.data} loading={market.isLoading} />

      {/* ============================================================ */}
      {/* Tabs + TF picker */}
      {/* ============================================================ */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-2">
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTab("analysis")}
            className={cn(
              "gap-1.5 rounded-b-none border-b-2 border-transparent",
              tab === "analysis" &&
                "border-emerald-500 bg-emerald-500/5 text-emerald-400 hover:bg-emerald-500/10",
            )}
          >
            <Activity className="h-3.5 w-3.5" />
            تحلیل تکنیکال
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTab("trade")}
            className={cn(
              "gap-1.5 rounded-b-none border-b-2 border-transparent",
              tab === "trade" &&
                "border-emerald-500 bg-emerald-500/5 text-emerald-400 hover:bg-emerald-500/10",
            )}
          >
            <BarChart3 className="h-3.5 w-3.5" />
            معامله و دفتر سفارش
          </Button>
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
        </div>
      </div>

      {/* ============================================================ */}
      {/* Tab: تحلیل تکنیکال */}
      {/* ============================================================ */}
      {tab === "analysis" && (
        <div className="space-y-5">
          {/* چارت پیشرفته + لینک چارت کامل */}
          {indicators.data && (
            <Card className="border-white/5 bg-[#0f0f17]">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 border-b border-white/5 pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <LineChart className="h-4 w-4 text-emerald-400" />
                  نمودار با اندیکاتورها
                </CardTitle>
                <Link href={`/markets/${symbol}/chart`}>
                  <Button
                    size="sm"
                    className="gap-1.5 bg-emerald-600 text-white hover:bg-emerald-500"
                  >
                    مشاهده‌ی چارت کامل
                    <ArrowUpRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </CardHeader>
              <CardContent className="pt-4">
                <SignalsChart
                  indicators={indicators.data}
                  levels={levels.data}
                  height={420}
                />
              </CardContent>
            </Card>
          )}

          {/* CTA */}
          <SignalCta symbol={symbol} variant="advanced" />

          {/* Confluence */}
          <ConfluenceCard
            data={multi.data?.confluence}
            loading={multi.isLoading}
          />

          {/* Multi-TF Grid */}
          <div>
            <h3 className="mb-3 flex items-center gap-2 text-sm font-bold">
              <Activity className="h-4 w-4 text-emerald-400" />
              سیگنال در تایم‌فریم‌ها
            </h3>
            <div className="grid gap-3 md:grid-cols-4">
              {TIMEFRAMES.map((tf) => (
                <MultiTfCard
                  key={tf}
                  timeframe={tf}
                  data={multi.data?.timeframes[tf]}
                  loading={multi.isLoading}
                  active={tf === timeframe}
                  onClick={() => setTimeframe(tf)}
                />
              ))}
            </div>
          </div>

          {/* اندیکاتورها */}
          <div>
            <h3 className="mb-3 flex items-center gap-2 text-sm font-bold">
              <Activity className="h-4 w-4 text-emerald-400" />
              اندیکاتورهای کلیدی
            </h3>
            <IndicatorsGrid
              data={indicators.data}
              loading={indicators.isLoading}
            />
          </div>

          {/* Rules Breakdown */}
          {signal.data && signal.data.rules && signal.data.rules.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-base">
                  <span className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-emerald-400" />
                    تجزیه‌ی قوانین سیگنال
                  </span>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className="border-emerald-500/30 bg-emerald-500/10 text-[10px] text-emerald-400"
                    >
                      🟢 خرید: {signal.data.buy_score}
                    </Badge>
                    <Badge
                      variant="outline"
                      className="border-red-500/30 bg-red-500/10 text-[10px] text-red-400"
                    >
                      🔴 فروش: {signal.data.sell_score}
                    </Badge>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {signal.data.rules.map((rule, i) => (
                    <RuleRow key={i} rule={rule} />
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Key Levels */}
          <div>
            <h3 className="mb-3 flex items-center gap-2 text-sm font-bold">
              📊 سطوح کلیدی
            </h3>
            <LevelsPanel symbol={symbol} timeframe={timeframe} />
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* Tab: معامله و دفتر سفارش */}
      {/* ============================================================ */}
      {tab === "trade" && (
        <div className="space-y-4">
          {/* Mini Chart */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <LineChart className="h-4 w-4 text-emerald-400" />
                نمودار قیمت
              </CardTitle>
            </CardHeader>
            <CardContent>
              {candles.isLoading ? (
                <Skeleton className="h-[240px] w-full" />
              ) : candles.data?.candles && candles.data.candles.length > 0 ? (
                <MiniChart candles={candles.data.candles} height={240} />
              ) : (
                <div className="flex h-[240px] items-center justify-center text-sm text-muted-foreground">
                  داده‌ای برای نمایش نیست
                </div>
              )}
            </CardContent>
          </Card>

          {/* Order Book Summary */}
          <OrderBookSummary
            bestBid={book.data?.best_bid}
            bestAsk={book.data?.best_ask}
            spread={book.data?.spread}
            spreadPct={book.data?.spread_pct}
            quoteAsset={market.data?.quote_asset ?? "—"}
            loading={book.isLoading}
          />

          {/* Order book tables */}
          <div className="grid gap-4 lg:grid-cols-2">
            <OrderBookTable
              title="خریداران (Bids)"
              levels={book.data?.bids ?? []}
              side="bid"
              loading={book.isLoading}
            />
            <OrderBookTable
              title="فروشندگان (Asks)"
              levels={book.data?.asks ?? []}
              side="ask"
              loading={book.isLoading}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// Order Book Table
// ============================================================

function OrderBookTable({
  title,
  levels,
  side,
  loading,
}: {
  title: string;
  levels: { price: string; quantity: string; sum: string }[];
  side: "bid" | "ask";
  loading: boolean;
}) {
  const accent = side === "bid" ? "text-emerald-400" : "text-red-400";
  const barColor = side === "bid" ? "bg-emerald-500/10" : "bg-red-500/10";
  const maxSum = Math.max(...levels.map((l) => Number(l.sum) || 0), 1);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <TrendingUp className={`h-4 w-4 ${accent}`} />
          {title}
        </CardTitle>
        <CardDescription>{levels.length} سطح قیمت</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-1">
            {[...Array(10)].map((_, i) => (
              <Skeleton key={i} className="h-7 w-full" />
            ))}
          </div>
        ) : (
          <div className="space-y-1">
            <div className="grid grid-cols-3 gap-2 px-2 pb-2 text-[11px] text-muted-foreground">
              <span>قیمت</span>
              <span className="text-left">مقدار</span>
              <span className="text-left">مجموع</span>
            </div>
            {levels.slice(0, 15).map((lvl, i) => (
              <div
                key={i}
                className="relative grid grid-cols-3 gap-2 rounded px-2 py-1.5 font-mono text-xs"
              >
                <div
                  className={`absolute inset-y-0 right-0 rounded ${barColor}`}
                  style={{ width: `${(Number(lvl.sum) / maxSum) * 100}%` }}
                />
                <span className={`relative z-10 font-semibold ${accent}`}>
                  {formatPrice(lvl.price)}
                </span>
                <span className="relative z-10 text-left text-muted-foreground">
                  {formatNumber(lvl.quantity, { maximumFractionDigits: 4 })}
                </span>
                <span className="relative z-10 text-left text-muted-foreground">
                  {formatNumber(lvl.sum, { maximumFractionDigits: 0 })}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
