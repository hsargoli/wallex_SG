"use client";

import Link from "next/link";
import { Zap, Wallet, ArrowUpRight, Play } from "lucide-react";
import { useUserPaperV3Status, useMarkets } from "@/lib/queries";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatNumber } from "@/lib/format";

export function ActionBar() {
  const paper = useUserPaperV3Status();
  const data = paper.data as Record<string, any> | undefined;
  
  const isRunning = data?.is_running ?? false;
  const capital = data?.capital ?? 0;
  const totalTrades = data?.total_trades ?? 0;
  const winRate = data?.win_rate ?? 0;
  const pnlPct = data?.total_pnl_pct ?? 0;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Paper Status */}
      <Card className="border-violet-500/20 bg-gradient-to-br from-violet-500/5 to-transparent">
        <CardContent className="pt-5">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/15">
              <Wallet className="h-4 w-4 text-violet-400" />
            </div>
            <Link href="/guest">
              <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground" />
            </Link>
          </div>
          <p className="text-[11px] text-muted-foreground">بودجه Paper</p>
          <p className="mt-1 text-xl font-bold text-violet-300">
            <span dir="ltr" className="font-mono">{formatNumber(capital, { maximumFractionDigits: 0 })}</span>
            <span className="mr-1 text-xs font-normal text-muted-foreground">TMN</span>
          </p>
          <p className="mt-1 text-[10px] text-muted-foreground">
            {isRunning ? "در حال اجرا" : "متوقف"} · {totalTrades} ترید · برد {winRate.toFixed(0)}%
          </p>
          {!isRunning && (
            <Button asChild variant="outline" size="sm" className="mt-2 w-full gap-2 border-violet-500/30 text-violet-300">
              <Link href="/guest">
                <Play className="h-3 w-3" />
                رفتن به Paper
              </Link>
            </Button>
          )}
        </CardContent>
      </Card>

      {/* PnL */}
      <Card className="border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 to-transparent">
        <CardContent className="pt-5">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/15">
              <Zap className="h-4 w-4 text-emerald-400" />
            </div>
            <Link href="/guest">
              <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground" />
            </Link>
          </div>
          <p className="text-[11px] text-muted-foreground">سود/زیان Paper</p>
          <p className={cn("mt-1 text-xl font-bold", pnlPct > 0 ? "text-emerald-400" : pnlPct < 0 ? "text-rose-400" : "text-muted-foreground")}>
            <span dir="ltr" className="font-mono">{pnlPct >= 0 ? "+" : ""}{pnlPct.toFixed(2)}%</span>
          </p>
          <p className="mt-1 text-[10px] text-muted-foreground">
            {totalTrades === 0 ? "هنوز تریدی انجام نشده" : `${totalTrades} ترید بسته‌شده`}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

import { cn } from "@/lib/utils";
