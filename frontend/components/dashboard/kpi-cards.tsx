"use client";

import Link from "next/link";
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  Bot,
  Coins,
  ArrowUpRight,
} from "lucide-react";
import { useWallet, usePortfolio, useBots, useBudget } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

// ---------- Helpers ----------

function calcTotalBalance(
  wallet: ReturnType<typeof useWallet>["data"],
  portfolio: ReturnType<typeof usePortfolio>["data"],
): { tmn: number; usdt: number; totalTmn: number } {
  // TMN آزاد
  const tmnBalance =
    wallet?.items?.find((b) => b.asset === "TMN")?.available || "0";
  const tmn = Number(tmnBalance);

  // ارزش کل سبد به TMN
  const portfolioValue = portfolio?.total_value_tmn_bid || "0";
  const totalTmn = Number(portfolioValue) || tmn;

  // USDT معادل
  const usdtRate = portfolio?.usdt_tmn_rate
    ? Number(portfolio.usdt_tmn_rate)
    : 0;
  const usdt = usdtRate > 0 ? totalTmn / usdtRate : 0;

  return { tmn, usdt, totalTmn };
}

// ---------- Component ----------

export function KpiCards() {
  const wallet = useWallet();
  const portfolio = usePortfolio();
  const bots = useBots();
  const budget = useBudget();

  const balances = calcTotalBalance(wallet.data, portfolio.data);
  const activeBots =
    bots.data?.bots?.filter((b) => b.status === "running").length || 0;
  const totalBots = bots.data?.count || 0;

  const budgetAllocated = Number(budget.data?.allocated_budget || 0);
  const budgetInUse = Number(budget.data?.in_use_capital || 0);
  const budgetFree = Number(budget.data?.available_for_trade || 0);
  const usagePct = budgetAllocated > 0 ? (budgetInUse / budgetAllocated) * 100 : 0;

  const isLoading =
    wallet.isLoading || portfolio.isLoading || bots.isLoading || budget.isLoading;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* ۱) موجودی کل */}
      <Link href="/portfolio" className="group">
        <Card className="h-full overflow-hidden border-emerald-500/20 bg-gradient-to-br from-emerald-500/[0.05] to-transparent transition-all hover:border-emerald-500/40 hover:shadow-lg hover:shadow-emerald-500/5">
          <CardContent className="pt-5">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/15">
                <Wallet className="h-4 w-4 text-emerald-400" />
              </div>
              <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
            </div>
            <p className="text-[11px] text-muted-foreground">موجودی کل (ارزش قابل برداشت)</p>
            {isLoading ? (
              <Skeleton className="mt-2 h-7 w-32" />
            ) : (
              <p className="mt-1 font-mono text-xl font-bold text-emerald-400">
                {formatNumber(balances.totalTmn)}{" "}
                <span className="text-xs text-muted-foreground">TMN</span>
              </p>
            )}
            <p className="mt-1 text-[10px] text-muted-foreground">
              ≈ {formatNumber(balances.usdt)} USDT
            </p>
          </CardContent>
        </Card>
      </Link>

      {/* ۲) بودجه */}
      <Link href="/budget" className="group">
        <Card className="h-full overflow-hidden border-amber-500/20 bg-gradient-to-br from-amber-500/[0.05] to-transparent transition-all hover:border-amber-500/40 hover:shadow-lg hover:shadow-amber-500/5">
          <CardContent className="pt-5">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/15">
                <Coins className="h-4 w-4 text-amber-400" />
              </div>
              <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
            </div>
            <p className="text-[11px] text-muted-foreground">سرمایه در گردش</p>
            {isLoading ? (
              <Skeleton className="mt-2 h-7 w-32" />
            ) : (
              <p className="mt-1 font-mono text-xl font-bold">
                {formatNumber(budgetInUse)}{" "}
                <span className="text-xs text-muted-foreground">TMN</span>
              </p>
            )}
            <div className="mt-1.5 flex items-center gap-2">
              <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/5">
                <div
                  className={cn(
                    "h-full rounded-full transition-all",
                    usagePct > 80
                      ? "bg-red-500"
                      : usagePct > 50
                        ? "bg-amber-500"
                        : "bg-emerald-500",
                  )}
                  style={{ width: `${Math.min(usagePct, 100)}%` }}
                />
              </div>
              <span className="font-mono text-[10px] text-muted-foreground">
                {usagePct.toFixed(0)}%
              </span>
            </div>
          </CardContent>
        </Card>
      </Link>

      {/* ۳) ربات‌ها */}
      <Link href="/bots" className="group">
        <Card className="h-full overflow-hidden border-blue-500/20 bg-gradient-to-br from-blue-500/[0.05] to-transparent transition-all hover:border-blue-500/40 hover:shadow-lg hover:shadow-blue-500/5">
          <CardContent className="pt-5">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/15">
                <Bot className="h-4 w-4 text-blue-400" />
              </div>
              <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
            </div>
            <p className="text-[11px] text-muted-foreground">ربات‌های فعال</p>
            {isLoading ? (
              <Skeleton className="mt-2 h-7 w-24" />
            ) : (
              <p className="mt-1 font-mono text-xl font-bold">
                {activeBots}{" "}
                <span className="text-sm text-muted-foreground">
                  از {totalBots}
                </span>
              </p>
            )}
            <p className="mt-1 flex items-center gap-1.5 text-[10px] text-muted-foreground">
              {activeBots > 0 ? (
                <>
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
                  {activeBots} ربات در حال کار
                </>
              ) : (
                <>
                  <span className="h-1.5 w-1.5 rounded-full bg-zinc-500" />
                  هیچ رباتی فعال نیست
                </>
              )}
            </p>
          </CardContent>
        </Card>
      </Link>

      {/* ۴) وضعیت اتصال */}
      <Link href="/orders" className="group">
        <Card className="h-full overflow-hidden border-violet-500/20 bg-gradient-to-br from-violet-500/[0.05] to-transparent transition-all hover:border-violet-500/40 hover:shadow-lg hover:shadow-violet-500/5">
          <CardContent className="pt-5">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/15">
                <TrendingUp className="h-4 w-4 text-violet-400" />
              </div>
              <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
            </div>
            <p className="text-[11px] text-muted-foreground">سود/زیان کل</p>
            <p className="mt-1 font-mono text-xl font-bold text-muted-foreground">
              —
            </p>
            <p className="mt-1 text-[10px] text-muted-foreground">
              به‌زودی در دسترس
            </p>
          </CardContent>
        </Card>
      </Link>
    </div>
  );
}
