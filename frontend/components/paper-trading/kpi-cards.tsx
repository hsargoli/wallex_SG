"use client";

import {
  Wallet,
  TrendingUp,
  TrendingDown,
  Target,
  Activity,
  ArrowUpRight,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { formatNumber } from "@/lib/format";

interface Props {
  data: any;
  isLoading: boolean;
}

export function PaperKpiCards({ data, isLoading }: Props) {
  const capital = Number(data?.equity ?? data?.capital ?? 0);
  const initial = Number(data?.initial_capital ?? 0);
  const pnl = Number(data?.total_pnl ?? 0);
  const pnlPct = Number(data?.total_pnl_pct ?? 0);
  const wr = Number(data?.win_rate ?? 0);
  const dd = Number(data?.max_drawdown_pct ?? 0);
  const isProfit = pnl >= 0;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* ۱) سرمایه */}
      <Card className="overflow-hidden border-blue-500/20 bg-gradient-to-br from-blue-500/[0.05] to-transparent">
        <CardContent className="pt-5">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/15">
              <Wallet className="h-4 w-4 text-blue-400" />
            </div>
          </div>
          <p className="text-[11px] text-muted-foreground">ارزش کل (Equity)</p>
          {isLoading ? (
            <Skeleton className="mt-2 h-7 w-32" />
          ) : (
            <p className="mt-1 font-mono text-xl font-bold text-blue-400">
              {formatNumber(capital)}{" "}
              <span className="text-xs text-muted-foreground">USDT</span>
            </p>
          )}
          <p className="mt-1 text-[10px] text-muted-foreground">
            از {formatNumber(initial)} USDT
          </p>
        </CardContent>
      </Card>

      {/* ۲) سود/زیان */}
      <Card
        className={cn(
          "overflow-hidden bg-gradient-to-br to-transparent",
          isProfit
            ? "border-emerald-500/20 from-emerald-500/[0.05]"
            : "border-red-500/20 from-red-500/[0.05]",
        )}
      >
        <CardContent className="pt-5">
          <div className="mb-3 flex items-center justify-between">
            <div
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded-lg",
                isProfit ? "bg-emerald-500/15" : "bg-red-500/15",
              )}
            >
              {isProfit ? (
                <TrendingUp className="h-4 w-4 text-emerald-400" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-400" />
              )}
            </div>
          </div>
          <p className="text-[11px] text-muted-foreground">سود/زیان کل</p>
          {isLoading ? (
            <Skeleton className="mt-2 h-7 w-32" />
          ) : (
            <p
              className={cn(
                "mt-1 font-mono text-xl font-bold",
                isProfit ? "text-emerald-400" : "text-red-400",
              )}
            >
              {isProfit ? "+" : ""}
              {pnlPct.toFixed(2)}
              <span className="text-xs">%</span>
            </p>
          )}
          <p className="mt-1 text-[10px] text-muted-foreground">
            {isProfit ? "+" : ""}
            {formatNumber(pnl)} USDT
          </p>
        </CardContent>
      </Card>

      {/* ۳) Win Rate */}
      <Card className="overflow-hidden border-amber-500/20 bg-gradient-to-br from-amber-500/[0.05] to-transparent">
        <CardContent className="pt-5">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/15">
              <Target className="h-4 w-4 text-amber-400" />
            </div>
          </div>
          <p className="text-[11px] text-muted-foreground">Win Rate</p>
          {isLoading ? (
            <Skeleton className="mt-2 h-7 w-24" />
          ) : (
            <p className="mt-1 font-mono text-xl font-bold text-amber-400">
              {wr.toFixed(1)}
              <span className="text-xs">%</span>
            </p>
          )}
          <p className="mt-1 text-[10px] text-muted-foreground">
            {data?.wins ?? 0}W / {data?.losses ?? 0}L
          </p>
        </CardContent>
      </Card>

      {/* ۴) Max DD */}
      <Card className="overflow-hidden border-violet-500/20 bg-gradient-to-br from-violet-500/[0.05] to-transparent">
        <CardContent className="pt-5">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/15">
              <Activity className="h-4 w-4 text-violet-400" />
            </div>
          </div>
          <p className="text-[11px] text-muted-foreground">Max Drawdown</p>
          {isLoading ? (
            <Skeleton className="mt-2 h-7 w-24" />
          ) : (
            <p className="mt-1 font-mono text-xl font-bold text-violet-400">
              {dd.toFixed(2)}
              <span className="text-xs">%</span>
            </p>
          )}
          <p className="mt-1 text-[10px] text-muted-foreground">
            {data?.total_trades ?? 0} ترید
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
