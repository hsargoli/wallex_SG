"use client";

import { TrendingUp, TrendingDown, Activity, BarChart3 } from "lucide-react";
import type { Market } from "@/lib/api";
import { formatNumber, formatPrice } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface MarketStatsProps {
  market: Market | null | undefined;
  loading?: boolean;
}

export function MarketStats({ market, loading }: MarketStatsProps) {
  if (loading || !market) {
    return (
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="h-20 animate-pulse rounded-lg border border-border/50 bg-card"
          />
        ))}
      </div>
    );
  }

  const change = Number(market.daily_change_percent || 0);
  const isUp = change >= 0;
  const isTMN = market.quote_asset === "TMN";
  const unit = isTMN ? "TMN" : "USDT";

  const stats = [
    {
      icon: isUp ? TrendingUp : TrendingDown,
      label: "تغییر ۲۴ ساعته",
      value: `${isUp ? "+" : ""}${change.toFixed(2)}%`,
      color: change === 0
        ? "text-muted-foreground"
        : isUp
          ? "text-emerald-400"
          : "text-red-400",
    },
    {
      icon: BarChart3,
      label: "قیمت آخر",
      value: market.last_price ? formatPrice(market.last_price) : "—",
      unit,
      color: "text-foreground",
    },
    {
      icon: Activity,
      label: "حجم ۲۴ ساعته",
      value: market.daily_volume
        ? formatNumber(market.daily_volume, { maximumFractionDigits: 2 })
        : "—",
      color: "text-blue-400",
    },
    {
      icon: BarChart3,
      label: "ارزش معاملات",
      value: market.daily_quote_volume
        ? formatNumber(market.daily_quote_volume, {
            maximumFractionDigits: 0,
          })
        : "—",
      unit,
      color: "text-amber-400",
    },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((s, i) => {
        const Icon = s.icon;
        return (
          <Card key={i} className="border-border/50">
            <CardContent className="pt-4">
              <div className="mb-2 flex items-center gap-2">
                <Icon
                  className={cn("h-3.5 w-3.5", s.color, "opacity-70")}
                />
                <span className="text-[10px] text-muted-foreground">
                  {s.label}
                </span>
              </div>
              <p className={cn("font-mono text-lg font-bold", s.color)}>
                {s.value}
                {s.unit && (
                  <span className="mr-1 text-[10px] text-muted-foreground">
                    {s.unit}
                  </span>
                )}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
