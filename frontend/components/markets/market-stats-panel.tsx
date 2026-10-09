"use client";

import { useState } from "react";
import {
  Activity,
  BarChart3,
  TrendingUp,
  TrendingDown,
  ArrowLeftRight,
  Percent,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarketOverview } from "@/lib/queries";
import { MoneyFlowCard } from "@/components/markets/money-flow-card";
import { CandleCountCard } from "@/components/markets/candle-count-card";
import type { MarketRange } from "@/lib/api";
import { formatPriceSmart } from "@/lib/format";
import { cn } from "@/lib/utils";

interface Props {
  symbol: string;
  timeframe?: string;
}

function fmtBig(v: string | number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  const n = Number(v);
  if (!Number.isFinite(n) || n === 0) return "—";
  const abs = Math.abs(n);
  if (abs >= 1_000_000_000_000) return `${(n / 1_000_000_000_000).toFixed(2)}T`;
  if (abs >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${(n / 1_000).toFixed(2)}K`;
  if (abs >= 1) return n.toFixed(2);
  return n.toFixed(6);
}

function StatRow({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: React.ReactNode;
  tone?: "default" | "emerald" | "red" | "muted";
}) {
  const toneCls =
    tone === "emerald"
      ? "text-emerald-400"
      : tone === "red"
        ? "text-red-400"
        : tone === "muted"
          ? "text-muted-foreground"
          : "text-foreground";
  return (
    <div className="flex items-center justify-between border-b border-border/30 py-2 last:border-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className={cn("font-mono text-xs font-bold", toneCls)}>{value}</span>
    </div>
  );
}

function RangeCard({ label, range }: { label: string; range: MarketRange | null }) {
  if (!range) {
    return (
      <Card className="border-white/5">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs text-muted-foreground">{label}</CardTitle>
        </CardHeader>
        <CardContent className="pb-3">
          <p className="text-xs text-muted-foreground">داده‌ی کافی نیست</p>
        </CardContent>
      </Card>
    );
  }

  const isUp = range.change_pct >= 0;
  return (
    <Card className="border-white/5">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">{label}</span>
          <span
            className={cn(
              "font-mono text-sm font-bold",
              isUp ? "text-emerald-400" : "text-red-400",
            )}
          >
            {isUp ? "+" : ""}
            {range.change_pct.toFixed(2)}%
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1 pb-3">
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-muted-foreground">بالاترین</span>
          <span className="font-mono text-emerald-400">
            {fmtBig(range.max)}
          </span>
        </div>
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-muted-foreground">پایین‌ترین</span>
          <span className="font-mono text-red-400">{fmtBig(range.min)}</span>
        </div>
      </CardContent>
    </Card>
  );
}

export function MarketStatsPanel({ symbol, timeframe = "1h" }: Props) {
  const q = useMarketOverview(symbol, timeframe);

  if (q.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (!q.data) return null;

  const { stats } = q.data;

  const spreadNum =
    stats.bid && stats.ask
      ? Number(stats.ask) - Number(stats.bid)
      : null;
  const spreadPct =
    spreadNum !== null && stats.bid && Number(stats.bid) > 0
      ? (spreadNum / Number(stats.bid)) * 100
      : null;

  const midPrice =
    stats.bid && stats.ask
      ? (Number(stats.bid) + Number(stats.ask)) / 2
      : null;
  const distFromHigh =
    midPrice && stats.high_24h
      ? ((midPrice - Number(stats.high_24h)) / Number(stats.high_24h)) * 100
      : null;
  const distFromLow =
    midPrice && stats.low_24h
      ? ((midPrice - Number(stats.low_24h)) / Number(stats.low_24h)) * 100
      : null;

  return (
    <div className="space-y-4">
      {/* ─── ۲۴ ساعت ─── */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Activity className="h-4 w-4 text-emerald-400" />
              ۲۴ ساعت اخیر
            </CardTitle>
          </CardHeader>
          <CardContent>
            <StatRow label="بالاترین" value={fmtBig(stats.high_24h)} tone="emerald" />
            <StatRow label="پایین‌ترین" value={fmtBig(stats.low_24h)} tone="red" />
            <StatRow
              label="فاصله از سقف"
              value={
                distFromHigh !== null ? (
                  <span className={distFromHigh >= 0 ? "text-emerald-400" : "text-red-400"}>
                    {distFromHigh >= 0 ? "+" : ""}
                    {distFromHigh.toFixed(2)}%
                  </span>
                ) : (
                  "—"
                )
              }
            />
            <StatRow
              label="فاصله از کف"
              value={
                distFromLow !== null ? (
                  <span className="text-emerald-400">
                    +{distFromLow.toFixed(2)}%
                  </span>
                ) : (
                  "—"
                )
              }
            />
            <StatRow
              label="تعداد معاملات"
              value={stats.trade_count ?? "—"}
            />
          </CardContent>
        </Card>

        {/* ─── حجم ─── */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <BarChart3 className="h-4 w-4 text-blue-400" />
              حجم معاملات
            </CardTitle>
          </CardHeader>
          <CardContent>
            <StatRow label="حجم ۲۴ ساعت" value={fmtBig(stats.volume_24h)} />
            <StatRow
              label="ارزش ۲۴ ساعت (TMN)"
              value={fmtBig(stats.quote_volume_24h)}
              tone="muted"
            />
            <StatRow label="حجم ۷ روز" value={fmtBig(stats.volume_7d)} />
          </CardContent>
        </Card>
      </div>

      {/* ─── دفتر سفارش ─── */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <ArrowLeftRight className="h-4 w-4 text-purple-400" />
            دفتر سفارش
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {/* خریداران */}
            <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/[0.03] p-3">
              <p className="mb-2 flex items-center gap-1.5 text-[11px] font-bold text-emerald-400">
                <TrendingUp className="h-3 w-3" />
                خریداران ({stats.bid_count ?? "—"} سفارش)
              </p>
              <StatRow label="قیمت" value={fmtBig(stats.bid)} tone="emerald" />
              <StatRow label="مقدار" value={fmtBig(stats.bid_volume)} tone="muted" />
            </div>

            {/* فروشندگان */}
            <div className="rounded-lg border border-red-500/20 bg-red-500/[0.03] p-3">
              <p className="mb-2 flex items-center gap-1.5 text-[11px] font-bold text-red-400">
                <TrendingDown className="h-3 w-3" />
                فروشندگان ({stats.ask_count ?? "—"} سفارش)
              </p>
              <StatRow label="قیمت" value={fmtBig(stats.ask)} tone="red" />
              <StatRow label="مقدار" value={fmtBig(stats.ask_volume)} tone="muted" />
            </div>
          </div>

          {/* Spread */}
          <div className="mt-4 rounded-lg border border-white/5 bg-background/40 p-3">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Percent className="h-3 w-3" />
                اسپرد
              </span>
              <div className="text-left">
                <p className="font-mono text-sm font-bold">
                  {spreadNum !== null ? formatPriceSmart(spreadNum) : "—"}
                </p>
                <p
                  className={cn(
                    "font-mono text-[10px]",
                    spreadPct !== null && spreadPct < 0.5
                      ? "text-emerald-400"
                      : spreadPct !== null && spreadPct < 1
                        ? "text-amber-400"
                        : "text-red-400",
                  )}
                >
                  {spreadPct !== null ? `${spreadPct.toFixed(3)}%` : "—"}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ─── جریان پول ─── */}
      <MoneyFlowCard data={q.data.money_flow} />

      {/* ─── کندل‌های سبز و قرمز ─── */}
      <CandleCountCard data={q.data.candle_count ?? null} />

      {/* ─── بازه‌های بلندمدت ─── */}
      <div>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-bold">
          <Activity className="h-4 w-4 text-emerald-400" />
          بازه‌های بلندمدت
        </h3>
        <div className="grid gap-3 md:grid-cols-3">
          <RangeCard label="۳۰ روز" range={stats.range_30d} />
          <RangeCard label="۹۰ روز" range={stats.range_90d} />
          <RangeCard label="۱ سال" range={stats.range_1y} />
        </div>
      </div>
    </div>
  );
}
