"use client";

import Link from "next/link";
import { TrendingUp, TrendingDown, ArrowUpRight, Flame } from "lucide-react";
import { useMarkets } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useMemo } from "react";

export function HotMarkets() {
  const markets = useMarkets();

  const topMarkets = useMemo(() => {
    if (!markets.data?.items) return [];
    return markets.data.items
      .filter((m) => m.quote_asset === "TMN" && m.last_price)
      .sort((a, b) => {
        const volA = Number(a.daily_quote_volume || 0);
        const volB = Number(b.daily_quote_volume || 0);
        return volB - volA;
      })
      .slice(0, 6);
  }, [markets.data]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Flame className="h-4 w-4 text-orange-400" />
            بازارهای داغ
          </span>
          <Link href="/markets">
            <Button variant="ghost" size="sm" className="gap-1 text-xs">
              همه بازارها
              <ArrowUpRight className="h-3 w-3" />
            </Button>
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-0.5">
        {markets.isLoading && (
          <>
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </>
        )}

        {topMarkets.map((m) => {
          const change = Number(m.daily_change_percent || 0);
          const isUp = change >= 0;
          return (
            <Link
              key={m.symbol}
              href={`/markets/${m.symbol}`}
              className="group flex items-center gap-3 rounded-lg border border-transparent px-3 py-2 transition-all hover:border-border hover:bg-white/[0.02]"
            >
              {/* Symbol */}
              <div className="min-w-0 flex-1">
                <p className="font-mono text-sm font-bold">{m.base_asset}</p>
                <p className="truncate text-[10px] text-muted-foreground">
                  {m.fa_name || m.en_name}
                </p>
              </div>

              {/* Price */}
              <div className="text-left">
                <p className="font-mono text-xs font-bold">
                  {formatNumber(m.last_price || 0)}
                </p>
                <p
                  className={cn(
                    "flex items-center justify-end gap-0.5 text-[10px] font-bold",
                    isUp ? "text-emerald-400" : "text-red-400",
                  )}
                >
                  {isUp ? (
                    <TrendingUp className="h-2.5 w-2.5" />
                  ) : (
                    <TrendingDown className="h-2.5 w-2.5" />
                  )}
                  {isUp ? "+" : ""}
                  {change.toFixed(2)}%
                </p>
              </div>
            </Link>
          );
        })}

        {!markets.isLoading && topMarkets.length === 0 && (
          <p className="py-8 text-center text-xs text-muted-foreground">
            داده‌ای موجود نیست
          </p>
        )}
      </CardContent>
    </Card>
  );
}
