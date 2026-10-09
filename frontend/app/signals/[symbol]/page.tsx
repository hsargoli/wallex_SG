"use client";

import { use, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Star,
  LineChart,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import {
  useSignal,
  useIndicators,
  useLevels,
  useMultiTfSignals,
  useMarket,
} from "@/lib/queries";
import { type Timeframe } from "@/lib/api";
import { SymbolSwitcher } from "@/components/markets/symbol-switcher";
import { useFavorites } from "@/lib/hooks/use-favorites";
import { formatPrice } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { SignalHero } from "@/components/signals/detail/signal-hero";
import { SignalCta } from "@/components/signals/detail/signal-cta";
import { BeginnerGuide } from "@/components/signals/detail/beginner-guide";
import { ConfluenceCard } from "@/components/signals/detail/confluence-card";
import { LevelsPanel } from "@/components/signals/levels-panel";
import { ChartPreview } from "@/components/charts/chart-preview";
import { MarketOverviewCard } from "@/components/markets/market-overview-card";
import { TechnicalSnapshotDetailed } from "@/components/signals/detail/technical-snapshot-detailed";
import { MoneyFlowCard } from "@/components/markets/money-flow-card";
import { useMarketOverview } from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const TIMEFRAMES: Timeframe[] = ["15m", "1h", "4h", "1D"];

export default function SignalDetailPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol: raw } = use(params);
  const symbol = raw.toUpperCase();
  const [timeframe, setTimeframe] = useState<Timeframe>("1h");

  const signal = useSignal(symbol, timeframe);
  const indicators = useIndicators(symbol, timeframe, 300);
  const multi = useMultiTfSignals(symbol);
  const levels = useLevels(symbol, timeframe);
  const market = useMarket(symbol);
  const overview = useMarketOverview(symbol, timeframe);
  const { isFavorite, toggle, mounted } = useFavorites();

  const change = Number(market.data?.daily_change_percent || 0);
  const isUp = change >= 0;
  const fav = mounted && isFavorite(symbol);

  return (
    <div className="space-y-5">
      {/* ─── Header: دقیقاً مثل market detail ─── */}
      <div className="flex flex-wrap items-center gap-4">
        <Link
          href="/signals"
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

        {/* Actions — دقیقاً مثل market detail */}
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
          <Link href={`/markets/${symbol}`}>
            <Button className="gap-2 bg-emerald-600 hover:bg-emerald-700">
              <BarChart3 className="h-4 w-4" />
              تحلیل حرفه‌ای
            </Button>
          </Link>
        </div>
      </div>

      {/* ─── SymbolSwitcher + TF Tabs (ردیف جدا) ─── */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SymbolSwitcher current={symbol} basePath="/signals" suffix="" />
        <div className="flex items-center gap-0.5 rounded-lg border border-border p-0.5">
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

      {/* ─── Signal Hero ─── */}
      <SignalHero
        symbol={symbol}
        timeframe={timeframe}
        signal={signal.data}
        loading={signal.isLoading}
      />

      {/* ─── نگاه کلی (compact) ─── */}
      <MarketOverviewCard symbol={symbol} timeframe={timeframe} compact beginner />

      {/* ─── Chart (۷۰٪) + Snapshot (۳۰٪) ─── */}
      <div
        className="grid gap-4"
        style={{ gridTemplateColumns: "minmax(0, 1fr) 340px" }}
      >
        {indicators.data && (
          <ChartPreview
            symbol={symbol}
            indicators={indicators.data}
            levels={levels.data}
            height={400}
            title="نمودار قیمت"
            visibleCandles={100}
          />
        )}

        <TechnicalSnapshotDetailed
          indicators={signal.data?.indicators ?? null}
          currentPrice={signal.data?.current_price ?? null}
          variant="beginner"
        />
      </div>

      {/* ─── MoneyFlow (simple) ─── */}
      <MoneyFlowCard data={overview.data?.money_flow ?? null} simple />

      {/* ─── Confluence ─── */}
      <ConfluenceCard data={multi.data?.confluence} loading={multi.isLoading} />

      {/* ─── Levels (compact) ─── */}
      <LevelsPanel symbol={symbol} timeframe={timeframe} compact />

      {/* ─── Beginner Guide ─── */}
      {signal.data && (
        <BeginnerGuide
          reasons={signal.data.reasons}
          signalType={signal.data.signal as "buy" | "sell" | "hold"}
        />
      )}

      {/* ─── CTA پایانی ─── */}
      <SignalCta symbol={symbol} />
    </div>
  );
}
