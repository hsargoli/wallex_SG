"use client";

import { useState } from "react";
import { Target, TrendingUp, TrendingDown, ChevronDown } from "lucide-react";
import { useLevels } from "@/lib/queries";
import { formatPrice, formatNumber } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function LevelsPanel({
  symbol,
  timeframe,
}: {
  symbol: string;
  timeframe: string;
}) {
  const levels = useLevels(symbol, timeframe);
  const [showPivot, setShowPivot] = useState(true);
  const [showSwings, setShowSwings] = useState(true);

  if (levels.isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!levels.data) return null;

  const { pivot, swings, current_price } = levels.data;
  const currentPrice = Number(current_price);

  return (
    <div className="space-y-4">
      {/* Pivot Points */}
      {pivot && (
        <Card>
          <CardHeader
            className="flex cursor-pointer flex-row items-center justify-between space-y-0 pb-3"
            onClick={() => setShowPivot((v) => !v)}
          >
            <CardTitle className="flex items-center gap-2 text-base">
              <Target className="h-5 w-5 text-emerald-400" />
              سطوح Pivot Point
            </CardTitle>
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform",
                !showPivot && "-rotate-90",
              )}
            />
          </CardHeader>
          {showPivot && (
            <CardContent>
              {/* Resistance side */}
              <div className="mb-3 space-y-1.5">
                <p className="text-[10px] font-medium text-muted-foreground">
                  مقاومت‌ها
                </p>
                <PivotRow label="R3" value={pivot.r3} current={currentPrice} color="text-red-400" />
                <PivotRow label="R2" value={pivot.r2} current={currentPrice} color="text-red-400" />
                <PivotRow label="R1" value={pivot.r1} current={currentPrice} color="text-red-400" />
              </div>

              {/* PP */}
              <div className="my-3">
                <PivotRow
                  label="PP"
                  value={pivot.pp}
                  current={currentPrice}
                  color="text-amber-400"
                  highlight
                />
              </div>

              {/* Support side */}
              <div className="space-y-1.5">
                <p className="text-[10px] font-medium text-muted-foreground">
                  حمایت‌ها
                </p>
                <PivotRow label="S1" value={pivot.s1} current={currentPrice} color="text-emerald-400" />
                <PivotRow label="S2" value={pivot.s2} current={currentPrice} color="text-emerald-400" />
                <PivotRow label="S3" value={pivot.s3} current={currentPrice} color="text-emerald-400" />
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Swing Levels */}
      {swings.length > 0 && (
        <Card>
          <CardHeader
            className="flex cursor-pointer flex-row items-center justify-between space-y-0 pb-3"
            onClick={() => setShowSwings((v) => !v)}
          >
            <CardTitle className="flex items-center gap-2 text-base">
              <TrendingUp className="h-5 w-5 text-emerald-400" />
              سطوح حمایت و مقاومت
              <Badge variant="outline" className="text-[10px]">
                {swings.length} سطح
              </Badge>
            </CardTitle>
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform",
                !showSwings && "-rotate-90",
              )}
            />
          </CardHeader>
          {showSwings && (
            <CardContent>
              <div className="space-y-1.5">
                {swings.map((swing, i) => (
                  <SwingRow key={i} swing={swing} current={currentPrice} />
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
}

function PivotRow({
  label,
  value,
  current,
  color,
  highlight,
}: {
  label: string;
  value: string;
  current: number;
  color: string;
  highlight?: boolean;
}) {
  const price = Number(value);
  const diffPct = ((current - price) / current) * 100;

  return (
    <div
      className={cn(
        "flex items-center justify-between rounded-lg border px-3 py-2",
        highlight
          ? "border-amber-500/30 bg-amber-500/5"
          : "border-white/5 bg-white/[0.02]",
      )}
    >
      <div className="flex items-center gap-2">
        <span className={cn("font-mono text-xs font-bold", color)}>
          {label}
        </span>
        <span className="font-mono text-sm">{formatPrice(value)}</span>
      </div>
      <span
        className={cn(
          "font-mono text-[10px]",
          diffPct >= 0 ? "text-emerald-400" : "text-red-400",
        )}
      >
        {diffPct >= 0 ? "+" : ""}
        {diffPct.toFixed(2)}%
      </span>
    </div>
  );
}

function SwingRow({
  swing,
  current,
}: {
  swing: {
    price: string;
    type: "support" | "resistance";
    touches: number;
    strength: "weak" | "medium" | "strong";
    distance_pct: string;
  };
  current: number;
}) {
  const isSupport = swing.type === "support";
  const Icon = isSupport ? TrendingUp : TrendingDown;
  const color = isSupport ? "text-emerald-400" : "text-red-400";
  const strengthLabel = {
    weak: "ضعیف",
    medium: "متوسط",
    strong: "قوی",
  }[swing.strength];
  const strengthColor = {
    weak: "border-white/10 text-zinc-400",
    medium: "border-amber-500/30 text-amber-400",
    strong: "border-emerald-500/30 text-emerald-400",
  }[swing.strength];

  return (
    <div className="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5">
      <div className="flex items-center gap-3">
        <Icon className={cn("h-4 w-4", color)} />
        <div>
          <p className={cn("font-mono text-sm font-semibold", color)}>
            {formatPrice(swing.price)}
          </p>
          <p className="text-[10px] text-muted-foreground">
            {isSupport ? "حمایت" : "مقاومت"} • {swing.touches} لمس
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="outline" className={cn("text-[10px]", strengthColor)}>
          {strengthLabel}
        </Badge>
        <span
          className={cn(
            "font-mono text-[10px]",
            Number(swing.distance_pct) >= 0 ? "text-emerald-400" : "text-red-400",
          )}
        >
          {Number(swing.distance_pct) >= 0 ? "+" : ""}
          {Number(swing.distance_pct).toFixed(2)}%
        </span>
      </div>
    </div>
  );
}
