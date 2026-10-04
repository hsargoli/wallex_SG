"use client";

import Link from "next/link";
import { TrendingUp, TrendingDown, Star } from "lucide-react";
import type { Market } from "@/lib/api";
import { formatNumber, formatPrice } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface MarketRowProps {
  market: Market;
  isFavorite: boolean;
  onToggleFavorite: (symbol: string) => void;
}

export function MarketRow({
  market,
  isFavorite,
  onToggleFavorite,
}: MarketRowProps) {
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
      className="group flex items-center gap-3 rounded-lg border border-border/50 bg-card px-3 py-2.5 transition-all hover:border-emerald-500/30 hover:bg-emerald-500/[0.03]"
    >
      {/* Star */}
      <button
        onClick={handleStar}
        className={cn(
          "shrink-0 rounded p-1 transition-colors",
          isFavorite
            ? "text-amber-400 hover:text-amber-300"
            : "text-muted-foreground/30 hover:text-amber-400",
        )}
        aria-label={isFavorite ? "حذف از علاقه‌مندی‌ها" : "افزودن به علاقه‌مندی‌ها"}
      >
        <Star
          className={cn("h-4 w-4", isFavorite && "fill-current")}
        />
      </button>

      {/* Base asset icon */}
      <div
        className={cn(
          "hidden h-9 w-9 shrink-0 items-center justify-center rounded-lg font-mono text-[10px] font-bold sm:flex",
          isTMN
            ? "bg-emerald-500/15 text-emerald-400"
            : "bg-blue-500/15 text-blue-400",
        )}
      >
        {market.base_asset.slice(0, 3)}
      </div>

      {/* Symbol + name */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="font-mono text-sm font-bold">{market.base_asset}</p>
          <Badge
            variant="outline"
            className={cn(
              "hidden text-[9px] sm:inline-flex",
              isTMN
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                : "border-blue-500/30 bg-blue-500/10 text-blue-400",
            )}
          >
            {market.quote_asset}
          </Badge>
        </div>
        <p className="truncate text-[10px] text-muted-foreground">
          {market.fa_name || market.en_name || "—"}
        </p>
      </div>

      {/* Price */}
      <div className="text-left">
        <p className="font-mono text-sm font-bold">
          {market.last_price ? formatPrice(market.last_price) : "—"}
        </p>
        {market.last_price && (
          <p className="font-mono text-[10px] text-muted-foreground">
            {isTMN ? "TMN" : "USDT"}
          </p>
        )}
      </div>

      {/* Change */}
      <div
        className={cn(
          "flex w-20 shrink-0 items-center justify-end gap-0.5 text-xs font-bold",
          change === 0
            ? "text-muted-foreground"
            : isUp
              ? "text-emerald-400"
              : "text-red-400",
        )}
      >
        {change !== 0 &&
          (isUp ? (
            <TrendingUp className="h-3 w-3" />
          ) : (
            <TrendingDown className="h-3 w-3" />
          ))}
        {change !== 0 ? `${isUp ? "+" : ""}${change.toFixed(2)}%` : "—"}
      </div>
    </Link>
  );
}
