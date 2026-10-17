"use client";

import Link from "next/link";
import { PieChart, ArrowUpRight, TrendingUp, TrendingDown } from "lucide-react";
import { useWallexStatus, useBatchSignals } from "@/lib/queries";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { useMemo } from "react";
import { formatNumber } from "@/lib/format";

export function PortfolioSignals() {
  const wallex = useWallexStatus();
  
  // استخراج دارایی‌های واقعی از والکس (بالای صفر)
  const assets = useMemo(() => {
    if (!wallex.data?.balances) return [];
    return wallex.data.balances
      .filter((b) => Number(b.total) > 0 && b.asset !== "TMN")
      .map((b) => `${b.asset}TMN`);
  }, [wallex.data]);

  const signals = useBatchSignals(assets, "1h");

  const signalMap = useMemo(() => {
    if (!signals.data?.signals) return {};
    const map: Record<string, any> = {};
    for (const s of signals.data.signals) {
      map[s.symbol] = s;
    }
    return map;
  }, [signals.data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <PieChart className="h-4 w-4 text-violet-400" />
            سیگنال دارایی‌های من (والکس)
          </span>
          <Link href="/signals">
            <Button variant="ghost" size="sm" className="gap-1 text-xs">
              مشاهده همه
              <ArrowUpRight className="h-3 w-3" />
            </Button>
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {wallex.isLoading && <Skeleton className="h-20 w-full" />}
        
        {!wallex.isLoading && assets.length === 0 && (
          <div className="flex flex-col items-center justify-center py-6 text-center text-muted-foreground">
            <PieChart className="mb-2 h-8 w-8 opacity-20" />
            <p className="text-sm">هنوز دارایی‌ای نداری</p>
            <Button asChild variant="outline" size="sm" className="mt-4">
              <Link href="/settings/wallex">اتصال به والکس</Link>
            </Button>
          </div>
        )}

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {assets.map((symbol) => {
            const sig = signalMap[symbol];
            const action = sig?.signal ?? "hold";
            const isBuy = action === "buy";
            const isSell = action === "sell";
            return (
              <div key={symbol} className="rounded-lg border border-white/10 bg-white/5 p-3">
                <div className="mb-2 flex items-center justify-between">
                  <Badge variant="outline" className="font-mono text-[10px]">{symbol}</Badge>
                  <span className="text-xs font-bold">{sig?.confidence ? `${sig.confidence}%` : "—"}</span>
                </div>
                <div className="flex items-center gap-2">
                  {isBuy && <TrendingUp className="h-4 w-4 text-emerald-400" />}
                  {isSell && <TrendingDown className="h-4 w-4 text-rose-400" />}
                  <span className={isBuy ? "text-sm text-emerald-400" : isSell ? "text-sm text-rose-400" : "text-sm text-muted-foreground"}>
                    {isBuy ? "خرید" : isSell ? "فروش" : "نگهداری"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
