"use client";

import Link from "next/link";
import { TrendingUp, TrendingDown, Star } from "lucide-react";
import type { Market } from "@/lib/api";
import { formatPrice, formatNumber } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface MarketCardProps {
  market: Market;
  isFavorite: boolean;
  onToggleFavorite: (symbol: string) => void;
}

export function MarketCard({
  market,
  isFavorite,
  onToggleFavorite,
}: MarketCardProps) {
  const change = Number(market.daily_change_percent || 0);
  const isUp = change >= 0;
  const isTMN = market.quote_asset === "TMN";

  const handleStar = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onToggleFavorite(market.symbol);
  };

  return (
    <Link
      href={`/markets/${market.symbol}`}
      className="group block rounded-xl border border-border/50 bg-card p-4 transition-all hover:border-emerald-500/30 hover:bg-emerald-500/[0.03] hover:shadow-lg hover:shadow-emerald-500/5"
    >
      {/* Header: icon + star */}
      <div className="mb-3 flex items-start justify-between">
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-lg font-mono text-xs font-bold",
            isTMN
              ? "bg-emerald-500/15 text-emerald-400"
              : "bg-blue-500/15 text-blue-400",
          )}
        >
          {market.base_asset.slice(0, 3)}
        </div>
        <button
          onClick={handleStar}
          className={cn(
            "rounded p-1 transition-colors",
            isFavorite
              ? "text-amber-400 hover:text-amber-300"
              : "text-muted-foreground/30 hover:text-amber-400",
          )}
          aria-label={isFavorite ? "حذف از علاقه‌مندی‌ها" : "افزودن به علاقه‌مندی‌ها"}
        >
          <Star className={cn("h-4 w-4", isFavorite && "fill-current")} />
        </button>
      </div>

      {/* Symbol */}
      <div className="mb-3">
        <div className="flex items-center gap-2">
          <p className="font-mono text-base font-bold">{market.base_asset}</p>
          <Badge
            variant="outline"
            className={cn(
              "text-[9px]",
              isTMN
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                : "border-blue-500/30 bg-blue-500/10 text-blue-400",
            )}
          >
            {market.quote_asset}
          </Badge>
        </div>
        <p className="truncate text-[11px] text-muted-foreground">
          {market.fa_name || market.en_name || "—"}
        </p>
      </div>

      {/* Price + change */}
      <div className="space-y-1">
        <p className="font-mono text-lg font-bold leading-tight">
          {market.last_price ? formatPrice(market.last_price) : "—"}
        </p>
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] text-muted-foreground">
            {isTMN ? "TMN" : "USDT"}
          </span>
          {change !== 0 && (
            <span
              className={cn(
                "flex items-center gap-0.5 font-mono text-xs font-bold",
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
          )}
        </div>
      </div>
    </Link>
  );
}
